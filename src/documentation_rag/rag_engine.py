"""
RAG Engine for Documentation Search

This module provides the core RAG functionality including document indexing,
embedding generation, and semantic search capabilities.
"""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .canvas_parser import CanvasParser


class RAGEngine:
    """RAG engine for document indexing and semantic search."""
    
    def __init__(self, vault_root: str, collection_name: str = "documentation"):
        """
        Initialize RAG engine.
        
        Args:
            vault_root: Path to Obsidian vault root
            collection_name: Name for ChromaDB collection
        """
        self.vault_root = Path(vault_root)
        self.collection_name = collection_name
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vault_root / ".rag_index"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Documentation RAG collection"}
        )
        
        # Initialize canvas parser
        self.canvas_parser = CanvasParser(str(self.vault_root))
    
    async def index_vault(self, force_reindex: bool = False) -> int:
        """
        Index all Canvas files and documents in the vault.
        
        Args:
            force_reindex: Whether to force re-indexing existing documents
            
        Returns:
            Number of documents indexed
        """
        if not force_reindex and self.collection.count() > 0:
            print(f"Collection already contains {self.collection.count()} documents. Use force_reindex=True to re-index.")
            return self.collection.count()
        
        if force_reindex:
            # Clear existing collection
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Documentation RAG collection"}
            )
        
        indexed_count = 0
        
        # Find all Canvas files
        canvas_files = list(self.vault_root.glob("**/*.canvas"))
        print(f"Found {len(canvas_files)} Canvas files to index")
        
        for canvas_file in canvas_files:
            try:
                indexed_count += await self._index_canvas_file(canvas_file)
            except Exception as e:
                print(f"Error indexing {canvas_file}: {e}")
        
        # Index standalone markdown files (not referenced by Canvas)
        md_files = list(self.vault_root.glob("**/*.md"))
        canvas_referenced_files = set()
        
        # Collect all files referenced by Canvas files
        for canvas_file in canvas_files:
            try:
                rel_path = canvas_file.relative_to(self.vault_root)
                canvas_data = self.canvas_parser.parse_canvas_file(str(rel_path))
                file_nodes = self.canvas_parser.get_file_nodes(canvas_data)
                for node in file_nodes:
                    canvas_referenced_files.add(self.vault_root / node["file"])
            except Exception as e:
                print(f"Error processing Canvas references in {canvas_file}: {e}")
        
        # Index standalone files
        standalone_files = [f for f in md_files if f not in canvas_referenced_files]
        print(f"Found {len(standalone_files)} standalone markdown files to index")
        
        for md_file in standalone_files:
            try:
                indexed_count += await self._index_standalone_file(md_file)
            except Exception as e:
                print(f"Error indexing standalone file {md_file}: {e}")
        
        print(f"Indexing complete. Total documents indexed: {indexed_count}")
        return indexed_count
    
    async def _index_canvas_file(self, canvas_file: Path) -> int:
        """Index a single Canvas file and its referenced documents."""
        rel_path = canvas_file.relative_to(self.vault_root)
        canvas_data = self.canvas_parser.parse_canvas_file(str(rel_path))
        
        indexed_count = 0
        documents = []
        metadatas = []
        ids = []
        
        # Index Canvas structure itself
        canvas_text = self._create_canvas_summary_text(canvas_data)
        canvas_id = f"canvas_{self._generate_id(str(rel_path))}"
        
        documents.append(canvas_text)
        metadatas.append({
            "source": str(rel_path),
            "type": "canvas",
            "title": canvas_file.stem
        })
        ids.append(canvas_id)
        
        # Index individual nodes with context
        for node in canvas_data.get("nodes", []):
            if node.get("type") == "text" and node.get("text"):
                # Create contextual text for the node
                contextual_text = self.canvas_parser.get_contextual_text_for_node(
                    node["id"], canvas_data
                )
                
                node_id_str = node["id"]
                node_id = f"node_{self._generate_id(f'{rel_path}_{node_id_str}')}"
                
                documents.append(contextual_text)
                metadatas.append({
                    "source": str(rel_path),
                    "type": "canvas_node",
                    "node_type": node.get("color", "0"),
                    "node_id": node["id"],
                    "title": f"{canvas_file.stem} - Node"
                })
                ids.append(node_id)
        
        # Index referenced files
        file_contents = self.canvas_parser.read_referenced_files(canvas_data)
        for file_path, content in file_contents.items():
            if content and not content.startswith("["):  # Skip error messages
                # Chunk large files
                chunks = self._chunk_text(content, max_chunk_size=1000)
                for i, chunk in enumerate(chunks):
                    chunk_id = f"file_{self._generate_id(f'{file_path}_chunk_{i}')}"
                    
                    documents.append(chunk)
                    metadatas.append({
                        "source": file_path,
                        "type": "file_chunk",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "canvas_source": str(rel_path),
                        "title": Path(file_path).stem
                    })
                    ids.append(chunk_id)
        
        # Batch add to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            indexed_count = len(documents)
        
        return indexed_count
    
    async def _index_standalone_file(self, file_path: Path) -> int:
        """Index a standalone file not referenced by any Canvas."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            return 0
        
        if not content.strip():
            return 0
        
        rel_path = file_path.relative_to(self.vault_root)
        chunks = self._chunk_text(content, max_chunk_size=1000)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"standalone_{self._generate_id(f'{rel_path}_chunk_{i}')}"
            
            documents.append(chunk)
            metadatas.append({
                "source": str(rel_path),
                "type": "standalone_file_chunk",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "title": file_path.stem
            })
            ids.append(chunk_id)
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        
        return len(documents)
    
    def _create_canvas_summary_text(self, canvas_data: Dict[str, Any]) -> str:
        """Create a summary text representation of the Canvas structure."""
        summary_parts = []
        
        # Add metadata
        metadata = canvas_data.get("metadata", {})
        summary_parts.append(f"Canvas Documentation: {canvas_data.get('canvas_path', 'Unknown')}")
        summary_parts.append(f"Total nodes: {metadata.get('total_nodes', 0)}, Total connections: {metadata.get('total_edges', 0)}")
        
        # Add color distribution info
        color_dist = metadata.get("color_distribution", {})
        color_legend = canvas_data.get("color_legend", {})
        
        for color, count in color_dist.items():
            meaning = color_legend.get(color, "Unknown")
            summary_parts.append(f"{meaning}: {count} items")
        
        # Add key nodes text
        nodes = canvas_data.get("nodes", [])
        text_nodes = [n for n in nodes if n.get("type") == "text" and n.get("text")]
        
        if text_nodes:
            summary_parts.append("Key components:")
            for node in text_nodes[:10]:  # Limit to first 10 nodes
                color = node.get("color", "0")
                node_type = color_legend.get(color, "Reference")
                summary_parts.append(f"- {node['text']} ({node_type})")
        
        return " | ".join(summary_parts)
    
    def _chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Split text into chunks for better embedding and retrieval.
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum size of each chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        
        # Split by paragraphs first
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
                
                # If paragraph itself is too long, split by sentences
                if len(paragraph) > max_chunk_size:
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
    
    def _generate_id(self, text: str) -> str:
        """Generate a unique ID for a document."""
        return hashlib.md5(text.encode()).hexdigest()
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search on indexed documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results with content and metadata
        """
        if self.collection.count() == 0:
            return []
        
        # Perform search
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
        
        # Format results
        formatted_results = []
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for doc, metadata, distance in zip(documents, metadatas, distances):
            # Convert distance to similarity score (ChromaDB uses cosine distance)
            similarity_score = 1 - distance
            
            formatted_results.append({
                "content": doc,
                "source": metadata.get("source", "Unknown"),
                "type": metadata.get("type", "unknown"),
                "title": metadata.get("title", "Untitled"),
                "score": similarity_score,
                "metadata": metadata
            })
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed collection."""
        count = self.collection.count()
        
        if count == 0:
            return {"total_documents": 0}
        
        # Get sample of metadata to analyze types
        sample_results = self.collection.get(limit=min(100, count), include=["metadatas"])
        
        type_counts = {}
        source_counts = {}
        
        for metadata in sample_results['metadatas']:
            doc_type = metadata.get("type", "unknown")
            source = metadata.get("source", "unknown")
            
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_documents": count,
            "document_types": type_counts,
            "top_sources": dict(list(source_counts.items())[:10])
        }
