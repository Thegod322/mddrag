#!/usr/bin/env python3

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import re

import mcp.types as types
from mcp import ClientSession, StdioServerParameters
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from documentation_rag.canvas_parser import CanvasParser

server = Server("documentation-rag-light")

class SimpleSearchEngine:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.documents = []
        self.canvas_parser = CanvasParser(str(vault_path))
    
    def index_documents(self):
        self.documents = []
        canvas_files = list(self.vault_path.glob("**/*.canvas"))
        
        for canvas_file in canvas_files:
            try:
                rel_path = canvas_file.relative_to(self.vault_path)
                canvas_data = self.canvas_parser.parse_canvas_file(str(rel_path))
                
                canvas_summary = self._create_canvas_summary(canvas_data)
                self.documents.append({
                    "content": canvas_summary,
                    "source": str(rel_path),
                    "type": "canvas",
                    "title": canvas_file.stem
                })
                
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
                
            except Exception as e:
                print(f"Error indexing {canvas_file}: {e}")
        
        return len(self.documents)
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.documents:
            return []
        
        query_lower = query.lower()
        query_words = re.findall(r'\w+', query_lower)
        
        scored_docs = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            score = 0
            
            if query_lower in content_lower:
                score += 10
            
            for word in query_words:
                if word in content_lower:
                    score += content_lower.count(word)
            
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
        
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:limit]
    
    def _create_canvas_summary(self, canvas_data: Dict[str, Any]) -> str:
        parts = []
        parts.append(f"Canvas: {canvas_data.get('canvas_path', 'Unknown')}")
        
        metadata = canvas_data.get("metadata", {})
        parts.append(f"Contains {metadata.get('total_nodes', 0)} nodes and {metadata.get('total_edges', 0)} connections")
        
        color_legend = canvas_data.get("color_legend", {})
        color_dist = metadata.get("color_distribution", {})
        
        for color, count in color_dist.items():
            meaning = color_legend.get(color, "Unknown")
            parts.append(f"{meaning}: {count} items")
        
        nodes = canvas_data.get("nodes", [])
        text_nodes = [n for n in nodes if n.get("type") == "text" and n.get("text")]
        
        if text_nodes:
            parts.append("Key components:")
            for node in text_nodes[:10]:
                parts.append(f"- {node['text']}")
        
        return " | ".join(parts)


search_engine = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_modular_documentation",
            description="Parse and retrieve modular documentation from Obsidian Canvas file",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {"type": "string"},
                    "canvas_file": {"type": "string"}
                },
                "required": ["vault_path", "canvas_file"]
            }
        ),
        types.Tool(
            name="get_file_content",
            description="Get content of a specific file from the Obsidian vault",
            inputSchema={
                "type": "object", 
                "properties": {
                    "vault_path": {"type": "string"},
                    "file_path": {"type": "string"}
                },
                "required": ["vault_path", "file_path"]
            }
        ),
        types.Tool(
            name="search_documentation",
            description="Search documentation using simple text matching",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "vault_path": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query", "vault_path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global search_engine
    
    if name == "get_modular_documentation":
        vault_path = arguments["vault_path"]
        canvas_file = arguments["canvas_file"]
        
        try:
            parser = CanvasParser(vault_path)
            canvas_data = parser.parse_canvas_file(canvas_file)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(canvas_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error parsing Canvas file: {str(e)}"
            )]
    
    elif name == "get_file_content":
        vault_path = arguments["vault_path"]
        file_path = arguments["file_path"]
        
        try:
            full_path = Path(vault_path) / file_path
            
            if not full_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"File not found: {file_path}"
                )]
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return [types.TextContent(
                type="text",
                text=content
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error reading file: {str(e)}"
            )]
    
    elif name == "search_documentation":
        query = arguments["query"]
        vault_path = arguments["vault_path"]
        limit = arguments.get("limit", 5)
        
        try:
            if not search_engine or search_engine.vault_path != Path(vault_path):
                search_engine = SimpleSearchEngine(vault_path)
                search_engine.index_documents()
            
            results = search_engine.search(query, limit)
            
            if not results:
                return [types.TextContent(
                    type="text",
                    text="No relevant documentation found for your query."
                )]
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"Result {i}:")
                formatted_results.append(f"Title: {result['title']}")
                formatted_results.append(f"Source: {result['source']}")
                formatted_results.append(f"Content: {result['content'][:300]}...")
                formatted_results.append("---")
            
            return [types.TextContent(
                type="text",
                text="\n".join(formatted_results)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error searching documentation: {str(e)}"
            )]
    
    else:
        return [types.TextContent(
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
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
