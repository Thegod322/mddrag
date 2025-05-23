#!/usr/bin/env python3
"""
Documentation RAG MCP Server

This server provides RAG capabilities for Obsidian Canvas-based modular documentation.
It can parse Canvas files, index their content, and provide semantic search functionality.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import chromadb
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl
from sentence_transformers import SentenceTransformer

from documentation_rag.canvas_parser import CanvasParser
from documentation_rag.rag_engine import RAGEngine

# Initialize the MCP server
server = Server("documentation-rag")

# Global variables for RAG engine and configurations
rag_engine: Optional[RAGEngine] = None
embedding_model: Optional[SentenceTransformer] = None
chroma_client: Optional[chromadb.Client] = None


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for documentation RAG."""
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
            name="search_documentation",
            description="Perform semantic search across indexed documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding relevant documentation"
                    },
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query", "vault_path"]
            }
        ),
        Tool(
            name="index_documentation",
            description="Index all Canvas files and associated documents in the vault for RAG search",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory"
                    },
                    "force_reindex": {
                        "type": "boolean",
                        "description": "Force re-indexing even if index exists (default: false)",
                        "default": False
                    }
                },
                "required": ["vault_path"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for documentation RAG operations."""
    
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
            
            if not full_path.is_file():
                return [TextContent(
                    type="text", 
                    text=f"Path is not a file: {file_path}"
                )]
            
            # Read file content
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
        force_reindex = arguments.get("force_reindex", False)
        
        try:
            # Initialize RAG engine if not already done
            global rag_engine
            if not rag_engine:
                rag_engine = RAGEngine(vault_path)
            
            # Index the documentation
            indexed_count = await rag_engine.index_vault(force_reindex)
            
            return [TextContent(
                type="text",
                text=f"Successfully indexed {indexed_count} documents from vault: {vault_path}"
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
            # Initialize RAG engine if not already done
            global rag_engine
            if not rag_engine:
                rag_engine = RAGEngine(vault_path)
                # Auto-index if no index exists
                await rag_engine.index_vault()
            
            # Perform search
            results = await rag_engine.search(query, limit)
            
            if not results:
                return [TextContent(
                    type="text",
                    text="No relevant documentation found for your query."
                )]
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"Result {i}:")
                formatted_results.append(f"Source: {result['source']}")
                formatted_results.append(f"Content: {result['content']}")
                formatted_results.append(f"Relevance Score: {result['score']:.3f}")
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
                server_name="documentation-rag",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
