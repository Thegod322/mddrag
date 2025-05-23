#!/usr/bin/env python3
"""
Lightweight Documentation RAG MCP Server

This version provides Canvas parsing and simple text search functionality
without heavy dependencies like ChromaDB.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import re
import hashlib

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import only the canvas parser
from documentation_rag.canvas_parser import CanvasParser

# Initialize the MCP server
server = Server("documentation-rag-light")


class SimpleSearchEngine:
    """Simple text-based search engine without vector embeddings."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.documents = []
        self.canvas_parser = CanvasParser(str(vault_path))
    
    def index_documents(self):
        """Index all Canvas files and documents for simple text search."""
        self.documents = []
        
        # Find all Canvas files
        canvas_files = list(self.vault_path.glob("**/*.canvas"))
        print(f"Found {len(canvas_files)} Canvas files to index")
        
        for canvas_file in canvas_files:
            try:
                rel_path = canvas_file.relative_to(self.vault_path)
                canvas_data = self.canvas_parser.parse_canvas_file(str(rel_path))
                
                # Index Canvas structure
                canvas_summary = self._create_canvas_summary(canvas_data)
                self.documents.append({
                    "content": canvas_summary,
                    "source": str(rel_path),
                    "type": "canvas",
                    "title": canvas_file.stem
                })
                
                # Index individual nodes
                for node in canvas_data.get("nodes", []):
                    if node.get("type") == "text" and node.get("text"):
                        contextual_text = self.canvas_parser.get_contextual_text_for_node(
                            node["id"], canvas_data
                        )
                        self.documents.append({
                            "content": contextual_text,
                            "source": str(rel_path),
                            "type": "canvas_node",
                            "title": f"{canvas_file.stem} - {node['text'][:30]}..."
                        })
                
                # Index referenced files
                file_contents = self.canvas_parser.read_referenced_files(canvas_data)
                for file_path, content in file_contents.items():
                    if content and not content.startswith("["):
                        # Split large files into chunks
                        chunks = self._chunk_text(content)
                        for i, chunk in enumerate(chunks):
                            self.documents.append({
                                "content": chunk,
                                "source": file_path,
                                "type": "file_chunk",
                                "title": f"{Path(file_path).stem} (part {i+1})"
                            })
                            
            except Exception as e:
                print(f"Error indexing {canvas_file}: {e}")
        
        # Index standalone markdown files
        md_files = list(self.vault_path.glob("**/*.md"))
        canvas_referenced_files = set()
        
        # Collect referenced files
        for canvas_file in canvas_files:
            try:
                rel_path = canvas_file.relative_to(self.vault_path)
                canvas_data = self.canvas_parser.parse_canvas_file(str(rel_path))
                file_nodes = self.canvas_parser.get_file_nodes(canvas_data)
                for node in file_nodes:
                    canvas_referenced_files.add(self.vault_path / node["file"])
            except:
                pass
        
        # Index standalone files
        standalone_files = [f for f in md_files if f not in canvas_referenced_files]
        for md_file in standalone_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.strip():
                    rel_path = md_file.relative_to(self.vault_path)
                    chunks = self._chunk_text(content)
                    for i, chunk in enumerate(chunks):
                        self.documents.append({
                            "content": chunk,
                            "source": str(rel_path),
                            "type": "standalone_file",
                            "title": f"{md_file.stem} (part {i+1})"
                        })
            except Exception as e:
                print(f"Error indexing {md_file}: {e}")
        
        print(f"Indexed {len(self.documents)} documents total")
        return len(self.documents)
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple text-based search."""
        if not self.documents:
            return []
        
        query_lower = query.lower()
        query_words = re.findall(r'\w+', query_lower)
        
        scored_docs = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            score = 0
            
            # Exact phrase match
            if query_lower in content_lower:
                score += 10
            
            # Word matches
            for word in query_words:
                if word in content_lower:
                    # Count occurrences
                    score += content_lower.count(word)
            
            # Title match bonus
            if any(word in doc["title"].lower() for word in query_words):
                score += 5
            
            if score > 0:
                scored_docs.append({
                    "content": doc["content"],
                    "source": doc["source"],
                    "type": doc["type"],
                    "title": doc["title"],
                    "score": score
                })
        
        # Sort by score and return top results
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:limit]
    
    def _create_canvas_summary(self, canvas_data: Dict[str, Any]) -> str:
        """Create a summary of Canvas structure."""
        parts = []
        parts.append(f"Canvas: {canvas_data.get('canvas_path', 'Unknown')}")
        
        metadata = canvas_data.get("metadata", {})
        parts.append(f"Contains {metadata.get('total_nodes', 0)} nodes and {metadata.get('total_edges', 0)} connections")
        
        # Add node types
        color_legend = canvas_data.get("color_legend", {})
        color_dist = metadata.get("color_distribution", {})
        
        for color, count in color_dist.items():
            meaning = color_legend.get(color, "Unknown")
            parts.append(f"{meaning}: {count} items")
        
        # Add key text nodes
        nodes = canvas_data.get("nodes", [])
        text_nodes = [n for n in nodes if n.get("type") == "text" and n.get("text")]
        
        if text_nodes:
            parts.append("Key components:")
            for node in text_nodes[:10]:
                parts.append(f"- {node['text']}")
        
        return " | ".join(parts)
    
    def _chunk_text(self, text: str, max_size: int = 1000) -> List[str]:
        """Split text into chunks."""
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if c.strip()]


# Global search engine instance
search_engine: Optional[SimpleSearchEngine] = None


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for lightweight documentation parsing."""
    return [
        Tool(
            name="get_modular_documentation",
            description="Parse and retrieve modular documentation from Obsidian Canvas file",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory"
                    },
                    "canvas_file": {
                        "type": "string", 
                        "description": "Relative path to the Canvas file from vault root (e.g., 'project.canvas')"
                    }
                },
                "required": ["vault_path", "canvas_file"]
            }
        ),
        Tool(
            name="get_file_content",
            description="Get content of a specific file from the Obsidian vault",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file from vault root"
                    }
                },
                "required": ["vault_path", "file_path"]
            }
        ),
        Tool(
            name="index_documentation",
            description="Index all Canvas files and documents for search (lightweight text-based indexing)",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory"
                    }
                },
                "required": ["vault_path"]
            }
        ),
        Tool(
            name="search_documentation",
            description="Search documentation using simple text matching",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query", "vault_path"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "get_modular_documentation":
        vault_path = arguments["vault_path"]
        canvas_file = arguments["canvas_file"]
        
        try:
            parser = CanvasParser(vault_path)
            canvas_data = parser.parse_canvas_file(canvas_file)
            
            return [TextContent(
                type="text",
                text=json.dumps(canvas_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error parsing Canvas file: {str(e)}"
            )]
    
    elif name == "get_file_content":
        vault_path = arguments["vault_path"]
        file_path = arguments["file_path"]
        
        try:
            full_path = Path(vault_path) / file_path
            
            if not full_path.exists():
                return [TextContent(
                    type="text",
                    text=f"File not found: {file_path}"
                )]
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return [TextContent(
                type="text",
                text=content
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error reading file: {str(e)}"
            )]
    
    elif name == "index_documentation":
        vault_path = arguments["vault_path"]
        
        try:
            global search_engine
            search_engine = SimpleSearchEngine(vault_path)
            doc_count = search_engine.index_documents()
            
            return [TextContent(
                type="text",
                text=f"Successfully indexed {doc_count} documents from vault: {vault_path}"
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error indexing documentation: {str(e)}"
            )]
    
    elif name == "search_documentation":
        query = arguments["query"]
        vault_path = arguments["vault_path"]
        limit = arguments.get("limit", 5)
        
        try:
            global search_engine
            if not search_engine or search_engine.vault_path != Path(vault_path):
                search_engine = SimpleSearchEngine(vault_path)
                search_engine.index_documents()
            
            results = search_engine.search(query, limit)
            
            if not results:
                return [TextContent(
                    type="text",
                    text="No relevant documentation found for your query."
                )]
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"Result {i}:")
                formatted_results.append(f"Title: {result['title']}")
                formatted_results.append(f"Source: {result['source']}")
                formatted_results.append(f"Type: {result['type']}")
                formatted_results.append(f"Score: {result['score']}")
                formatted_results.append(f"Content: {result['content'][:500]}...")
                formatted_results.append("---")
            
            return [TextContent(
                type="text",
                text="\n".join(formatted_results)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error searching documentation: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Main entry point for the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="documentation-rag-light",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
