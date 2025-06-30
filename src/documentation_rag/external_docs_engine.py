def _batched_add_to_collection(collection, documents, embeddings, metadatas, ids, batch_size=5461):
    """
    Add documents to ChromaDB collection in batches to avoid ValueError on large files.
    """
    total = len(documents)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        collection.add(
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end]
        )
"""
External Documentation RAG Engine

This module provides functionality to index and search external documentation
(libraries, frameworks, tools) separately from Obsidian vault content.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class ExternalDocsEngine:
    def get_stats(self) -> dict:
        """
        Return statistics about the libraries_docs ChromaDB collection.
        """
        count = self.collection.count()
        stats = {
            "total_documents": count,
            "collections": {}
        }
        if count == 0:
            return stats
        # Get a sample of metadata to analyze types and sources
        sample = self.collection.get(limit=min(100, count), include=["metadatas"])
        source_counts = {}
        doc_types = {}
        docs = set()
        for meta in sample["metadatas"]:
            source = meta.get("source", "unknown")
            file_name = meta.get("file_name", "unknown")
            doc_type = meta.get("doc_type", "unknown")
            docs.add(file_name)
            source_counts[source] = source_counts.get(source, 0) + 1
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        stats["collections"]["libraries_docs"] = {
            "document_count": count,
            "sources": source_counts,
            "doc_types": doc_types,
            "docs": list(docs)
        }
        return stats
    """RAG engine for external documentation management."""
    
    def __init__(self, libraries_path: str = None):
        """
        Initialize engine for indexing and searching Libraries directory only.
        Args:
            libraries_path: Path to Libraries directory (default: ./Libraries)
        """
        if libraries_path is None:
            libraries_path = Path.cwd() / "Libraries"
        self.libraries_path = Path(libraries_path)
        self.libraries_path.mkdir(exist_ok=True)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(
            path=str(Path.home() / ".documentation_rag" / "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="libraries_docs",
            metadata={"description": "Documentation indexed from Libraries directory"}
        )
    
    async def index_libraries(self, force_reindex: bool = False) -> int:
        """
        Index all files in the Libraries directory. Supported: .md, .txt, .rst, .html, .jsonl
        If force_reindex=True, clears the collection first.
        Returns number of documents indexed.
        """
        if force_reindex:
            self.chroma_client.delete_collection("libraries_docs")
            self.collection = self.chroma_client.get_or_create_collection(
                name="libraries_docs",
                metadata={"description": "Documentation indexed from Libraries directory"}
            )
        files_to_process = []
        for ext in ['*.md', '*.txt', '*.rst', '*.html']:
            files_to_process.extend(self.libraries_path.rglob(ext))
        jsonl_files = list(self.libraries_path.rglob('*.jsonl'))
        print(f"Found {len(files_to_process)} text/rst/html/md files and {len(jsonl_files)} jsonl files to index in Libraries")
        indexed_count = 0
        # Index regular text files
        for file_path in files_to_process:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if not content.strip():
                    continue
                chunks = self._chunk_text(content, max_chunk_size=1000)
                documents = []
                metadatas = []
                ids = []
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_path.stem}_{i}"
                    documents.append(chunk)
                    metadatas.append({
                        "source": str(file_path),
                        "file_name": file_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    })
                    ids.append(chunk_id)
                if documents:
                    embeddings = self.embedding_model.encode(documents).tolist()
                    _batched_add_to_collection(
                        self.collection, documents, embeddings, metadatas, ids
                    )
                    indexed_count += len(documents)
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")
        # Index .jsonl files (each line is a JSON object with at least a 'text' field)
        for jsonl_path in jsonl_files:
            try:
                with open(jsonl_path, 'r', encoding='utf-8') as f:
                    documents = []
                    metadatas = []
                    ids = []
                    for idx, line in enumerate(f):
                        try:
                            obj = json.loads(line)
                            text = obj.get('text', '').strip()
                            if not text:
                                continue
                            chunk_id = f"{jsonl_path.stem}_{idx}"
                            documents.append(text)
                            meta = {
                                "source": str(jsonl_path),
                                "file_name": obj.get('file', jsonl_path.name),
                                "section": obj.get('section', ''),
                                "chunk_index": idx
                            }
                            metadatas.append(meta)
                            ids.append(chunk_id)
                        except Exception as e:
                            print(f"Malformed line in {jsonl_path} at {idx}: {e}")
                    if documents:
                        embeddings = self.embedding_model.encode(documents).tolist()
                        _batched_add_to_collection(
                            self.collection, documents, embeddings, metadatas, ids
                        )
                        indexed_count += len(documents)
            except Exception as e:
                print(f"Error indexing jsonl file {jsonl_path}: {e}")
        print(f"Indexing complete. Total documents indexed: {indexed_count}")
        return indexed_count
    
    async def _index_single_file(
        self, 
        file_path: Path, 
        collection, 
        doc_name: str, 
        version: str,
        doc_type: str
    ) -> int:
        """Index a single documentation file."""
        try:
            # Read file content
            if file_path.suffix == '.html':
                # Simple HTML stripping (you might want to use BeautifulSoup for better parsing)
                import re
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = re.sub('<[^<]+?>', '', content)  # Remove HTML tags
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            return 0
        
        if not content.strip():
            return 0
        
        # Chunk the content
        chunks = self._chunk_text(content, max_chunk_size=1000)
        
        documents = []
        metadatas = []
        ids = []
        
        rel_path = file_path.relative_to(file_path.parent.parent) if file_path.parent.parent.exists() else file_path.name
        
        for i, chunk in enumerate(chunks):
            chunk_id = self._generate_id(f"{doc_name}_{version}_{rel_path}_{i}")
            
            documents.append(chunk)
            metadatas.append({
                "source": str(rel_path),
                "doc_name": doc_name,
                "doc_type": doc_type,
                "version": version,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "file_name": file_path.name,
                "indexed_at": datetime.now().isoformat()
            })
            ids.append(chunk_id)
        
        if documents:
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Add to collection
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        
        return len(documents)
    
    def _chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into chunks."""
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                if len(paragraph) > max_chunk_size:
                    # Split by sentences
                    sentences = paragraph.split('. ')
                    temp_chunk = ""
                    
                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) + 2 <= max_chunk_size:
                            if temp_chunk:
                                temp_chunk += ". " + sentence
                            else:
                                temp_chunk = sentence
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = sentence
                    
                    current_chunk = temp_chunk
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if c.strip()]

    async def search(self, query: str, limit: int = 5) -> List[dict]:
        """
        Semantic search in the Libraries collection.
        Args:
            query: Search query
            limit: Max results
        Returns:
            List of search results with content and metadata
        """
        if self.collection.count() == 0:
            return []
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        if not results['documents'] or not results['documents'][0]:
            return []
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        formatted_results = []
        for doc, metadata, distance in zip(documents, metadatas, distances):
            similarity_score = 1 - distance
            formatted_results.append({
                "content": doc,
                "score": similarity_score,
                "source": metadata.get("source", "Unknown"),
                "file_name": metadata.get("file_name", "Unknown"),
                "chunk_index": metadata.get("chunk_index", -1),
                "total_chunks": metadata.get("total_chunks", -1),
                "metadata": metadata
            })
        return formatted_results
    
    # All metadata/statistics/management methods removed for simplicity
