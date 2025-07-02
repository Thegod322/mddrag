#!/usr/bin/env python3
"""
Documentation RAG MCP Server (Unified)

This server provides RAG capabilities for:
1. Obsidian Canvas-based modular documentation (MDD method)
2. External documentation libraries indexed in ChromaDB
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
from mcp.server.lowlevel import NotificationOptions
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
from documentation_rag.external_docs_engine import ExternalDocsEngine
from documentation_rag.vaultpicker_bridge import get_current_vault_path

# Initialize the MCP server
server = Server("documentation-rag")

# Global variables for engines
rag_engine: Optional[RAGEngine] = None
external_docs_engine: Optional[ExternalDocsEngine] = None


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for documentation RAG."""
    return [
        # === Obsidian Canvas / MDD Tools ===
        Tool(
            name="get_modular_documentation",
            description="Parse and retrieve modular documentation from Obsidian Canvas file",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory (optional, auto from VaultPicker if not set)"
                    },
                    "canvas_file": {
                        "type": "string",
                        "description": "Relative path to the Canvas file from vault root (e.g., 'project.canvas')"
                    }
                },
                "required": ["canvas_file"]
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
                        "description": "Path to the Obsidian vault root directory (optional, auto from VaultPicker if not set)"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file from vault root"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="index_obsidian_vault",
            description="Index Obsidian vault documents for RAG search (project documentation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory (optional, auto from VaultPicker if not set)"
                    },
                    "force_reindex": {
                        "type": "boolean",
                        "description": "Force re-indexing even if index exists (default: false)",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_obsidian_docs",
            description="Search in Obsidian vault documentation (project-specific)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory (optional, auto from VaultPicker if not set)"
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        
        # === ChromaDB / External Libraries Tools ===
        Tool(
            name="search_documentation",
            description="Search in external documentation indexed in ChromaDB (libraries, frameworks, tools)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="load_external_docs",
            description="Load external documentation into ChromaDB index",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_path": {
                        "type": "string",
                        "description": "Path to documentation files"
                    },
                    "doc_name": {
                        "type": "string",
                        "description": "Name identifier for the documentation"
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Type of documentation (library, framework, tool, etc.)",
                        "default": "general"
                    },
                    "version": {
                        "type": "string",
                        "description": "Version of the documentation",
                        "default": "latest"
                    },
                    "force_reindex": {
                        "type": "boolean",
                        "description": "Force re-indexing even if already exists",
                        "default": False
                    }
                },
                "required": ["doc_path", "doc_name"]
            }
        ),
        Tool(
            name="list_loaded_docs",
            description="List all external documentation loaded in ChromaDB",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="remove_external_docs",
            description="Remove external documentation from ChromaDB index",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_name": {
                        "type": "string",
                        "description": "Name of documentation to remove"
                    },
                    "version": {
                        "type": "string",
                        "description": "Version to remove (default: latest)",
                        "default": "latest"
                    }
                },
                "required": ["doc_name"]
            }
        ),
        Tool(
            name="get_docs_stats",
            description="Get statistics about indexed documentation in ChromaDB",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for documentation RAG operations."""
    global rag_engine, external_docs_engine
    
    # === Obsidian Canvas / MDD Tools ===
    if name == "get_modular_documentation":
        vault_path = arguments.get("vault_path")
        canvas_file = arguments["canvas_file"]
        if not vault_path:
            vault_path = get_current_vault_path()
        if not vault_path:
            return [TextContent(type="text", text="Vault path not found! Please set active vault in VaultPicker.")]
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
        vault_path = arguments.get("vault_path")
        file_path = arguments["file_path"]
        if not vault_path:
            vault_path = get_current_vault_path()
        if not vault_path:
            return [TextContent(type="text", text="Vault path not found! Please set active vault in VaultPicker.")]
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
    
    elif name == "index_obsidian_vault":
        vault_path = arguments.get("vault_path")
        force_reindex = arguments.get("force_reindex", False)
        if not vault_path:
            vault_path = get_current_vault_path()
        if not vault_path:
            return [TextContent(type="text", text="Vault path not found! Please set active vault in VaultPicker.")]
        try:
            if not rag_engine:
                rag_engine = RAGEngine(vault_path)
            indexed_count = await rag_engine.index_vault(force_reindex)
            return [TextContent(
                type="text",
                text=f"Successfully indexed {indexed_count} documents from Obsidian vault: {vault_path}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error indexing Obsidian vault: {str(e)}"
            )]
    
    elif name == "search_obsidian_docs":
        query = arguments["query"]
        vault_path = arguments.get("vault_path")
        limit = arguments.get("limit", 5)
        if not vault_path:
            vault_path = get_current_vault_path()
        if not vault_path:
            return [TextContent(type="text", text="Vault path not found! Please set active vault in VaultPicker.")]
        try:
            if not rag_engine:
                rag_engine = RAGEngine(vault_path)
                await rag_engine.index_vault()
            results = await rag_engine.search(query, limit)
            if not results:
                return [TextContent(
                    type="text",
                    text="No relevant documentation found in Obsidian vault."
                )]
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
                text=f"Error searching Obsidian documentation: {str(e)}"
            )]
    
    # === ChromaDB / External Libraries Tools ===
    elif name == "search_documentation":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        
        try:
            if not external_docs_engine:
                external_docs_engine = ExternalDocsEngine()
            
            results = await external_docs_engine.search(query, limit)
            
            if not results:
                return [TextContent(
                    type="text",
                    text="No relevant documentation found in external libraries."
                )]
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"Result {i}:")
                formatted_results.append(f"Source: {result.get('source', 'Unknown')}")
                formatted_results.append(f"Content: {result.get('content', result.get('text', ''))}")
                if 'score' in result:
                    formatted_results.append(f"Relevance Score: {result['score']:.3f}")
                formatted_results.append("---")
                
            return [TextContent(
                type="text",
                text="\n".join(formatted_results)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error searching external documentation: {str(e)}"
            )]
    
    elif name == "load_external_docs":
        doc_path = arguments["doc_path"]
        doc_name = arguments["doc_name"]
        doc_type = arguments.get("doc_type", "general")
        version = arguments.get("version", "latest")
        force_reindex = arguments.get("force_reindex", False)
        
        try:
            if not external_docs_engine:
                external_docs_engine = ExternalDocsEngine()
            
            result = await external_docs_engine.index_documentation(
                doc_path=doc_path,
                doc_name=doc_name,
                doc_type=doc_type,
                version=version,
                force_reindex=force_reindex
            )
            
            if "error" in result:
                return [TextContent(
                    type="text",
                    text=f"Error: {result['error']}"
                )]
            
            if result["status"] == "already_indexed":
                info = result["info"]
                return [TextContent(
                    type="text",
                    text=f"Documentation '{doc_name}' v{version} is already indexed.\n"
                         f"Indexed at: {info['indexed_at']}\n"
                         f"Documents: {info['document_count']}\n"
                         f"Use force_reindex=true to re-index."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Successfully indexed '{doc_name}' v{version}\n"
                         f"Documents processed: {result.get('document_count', 'Unknown')}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error loading external documentation: {str(e)}"
            )]
    
    elif name == "list_loaded_docs":
        try:
            if not external_docs_engine:
                external_docs_engine = ExternalDocsEngine()
            
            docs_info = external_docs_engine.list_indexed_docs()
            
            if not docs_info["indexed_docs"]:
                return [TextContent(
                    type="text",
                    text="No external documentation loaded yet."
                )]
            
            formatted = [f"Total documents: {docs_info['total_documents']}"]
            formatted.append(f"Last updated: {docs_info['last_updated'] or 'Never'}")
            formatted.append("\nLoaded documentation:")
            
            for key, info in docs_info["indexed_docs"].items():
                formatted.append(f"\n- {info['name']} v{info['version']}")
                formatted.append(f"  Type: {info['type']}")
                formatted.append(f"  Documents: {info['document_count']}")
                formatted.append(f"  Indexed: {info['indexed_at']}")
                formatted.append(f"  Source: {info['source_path']}")
            
            return [TextContent(
                type="text",
                text="\n".join(formatted)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error listing documentation: {str(e)}"
            )]
    
    elif name == "remove_external_docs":
        doc_name = arguments["doc_name"]
        version = arguments.get("version", "latest")
        
        try:
            if not external_docs_engine:
                external_docs_engine = ExternalDocsEngine()
            
            success = external_docs_engine.remove_documentation(doc_name, version)
            
            if success:
                return [TextContent(
                    type="text",
                    text=f"Successfully removed '{doc_name}' v{version} from index."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Documentation '{doc_name}' v{version} not found in index."
                )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error removing documentation: {str(e)}"
            )]
    
    elif name == "get_docs_stats":
        try:
            if not external_docs_engine:
                external_docs_engine = ExternalDocsEngine()
            
            stats = external_docs_engine.get_stats()
            
            formatted = [f"Total indexed documents: {stats['total_documents']}\n"]
            formatted.append("Collections:")
            
            for coll_name, coll_info in stats["collections"].items():
                formatted.append(f"\n{coll_name.upper()}:")
                formatted.append(f"  Document chunks: {coll_info['document_count']}")
                if coll_info['docs']:
                    formatted.append("  Contains:")
                    for doc in coll_info['docs']:
                        formatted.append(f"    - {doc}")
            
            return [TextContent(
                type="text",
                text="\n".join(formatted)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting statistics: {str(e)}"
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
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities=None,
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
