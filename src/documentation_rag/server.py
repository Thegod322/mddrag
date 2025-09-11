#!/usr/bin/env python3
"""
Documentation RAG MCP Server (Simplified)

This server provides a simple RAG interface for LLM agents with 4 core tools:
1. get_modular_documentation - Parse MDD Canvas files
2. print_mdd - Parse and save MDD Canvas files to .MDD files
3. get_file_content - Read vault files 
4. search_documentation - Search external docs in ChromaDB
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the src directory to Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel import NotificationOptions
from mcp.types import (
    Tool,
    TextContent,
)

# Import modules using absolute imports after setting up the path
from documentation_rag.canvas_parser import CanvasParser
from documentation_rag.external_docs_engine import ExternalDocsEngine
from documentation_rag.vaultpicker_bridge import get_current_vault_path

# Initialize the MCP server
server = Server("documentation-rag")

# Global external docs engine
external_docs_engine: Optional[ExternalDocsEngine] = None


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List the 4 core RAG tools for LLM agents."""
    return [
        Tool(
            name="get_modular_documentation",
            description="Parse and retrieve modular documentation from Obsidian Canvas file. Automatically searches for the canvas file recursively in the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory (optional, auto from VaultPicker if not set)"
                    },
                    "canvas_file": {
                        "type": "string",
                        "description": "Name of the Canvas file (e.g., 'Documentation-rag_MDD.canvas'). The file will be found automatically in the vault."
                    }
                },
                "required": ["canvas_file"]
            }
        ),
        Tool(
            name="print_mdd",
            description="Parse modular documentation from Obsidian Canvas file and save it to a specified output path with .MDD extension. Works exactly like get_modular_documentation but saves to file instead of returning data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vault_path": {
                        "type": "string",
                        "description": "Path to the Obsidian vault root directory (optional, auto from VaultPicker if not set)"
                    },
                    "canvas_file": {
                        "type": "string",
                        "description": "Name of the Canvas file (e.g., 'Documentation-rag_MDD.canvas'). The file will be found automatically in the vault."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path where to save the MDD file. The .MDD extension will be automatically added if not present."
                    }
                },
                "required": ["canvas_file", "output_path"]
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
            name="search_documentation",
            description="Search in external documentation indexed in ChromaDB (libraries, frameworks, tools)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in human language"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle the 4 core tool calls."""
    global external_docs_engine
    
    if name == "get_modular_documentation":
        vault_path = arguments.get("vault_path")
        canvas_file = arguments["canvas_file"]
        if not vault_path:
            vault_path = get_current_vault_path()
        if not vault_path:
            return [TextContent(type="text", text="Vault path not found! Please set active vault in VaultPicker.")]
        try:
            parser = CanvasParser(vault_path)
            # Use new auto-search functionality
            canvas_data = parser.parse_canvas_auto(canvas_file)
            return [TextContent(
                type="text",
                text=json.dumps(canvas_data, indent=2, ensure_ascii=False)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error parsing Canvas file: {str(e)}"
            )]
    
    elif name == "print_mdd":
        vault_path = arguments.get("vault_path")
        canvas_file = arguments["canvas_file"]
        output_path = arguments["output_path"]
        
        if not vault_path:
            vault_path = get_current_vault_path()
        if not vault_path:
            return [TextContent(type="text", text="Vault path not found! Please set active vault in VaultPicker.")]
        
        # Ensure output path has .MDD extension
        if not output_path.lower().endswith('.mdd'):
            output_path = output_path + '.MDD'
        
        try:
            parser = CanvasParser(vault_path)
            # Use new auto-search functionality
            canvas_data = parser.parse_canvas_auto(canvas_file)
            
            # Convert to JSON and save to file
            json_data = json.dumps(canvas_data, indent=2, ensure_ascii=False)
            
            # Create directory if it doesn't exist
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            return [TextContent(
                type="text",
                text=f"MDD successfully saved to: {output_path}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error processing or saving MDD file: {str(e)}"
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
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}. Available tools: get_modular_documentation, print_mdd, get_file_content, search_documentation"
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
                    experimental_capabilities=None
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
