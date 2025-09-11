#!/usr/bin/env python3
"""
Documentation RAG MCP Server (Simplified)

This server provides a simple RAG interface for LLM agents with 4 core tools:
1. get_modular_documentation - Parse MDD Canvas files
2. print_mdd - Parse and save MDD Canvas files to .MDD files (enhanced: standalone export)
3. get_file_content - Read vault files 
4. search_documentation - Search external docs in ChromaDB
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import shutil

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

# ----------------- Helper Functions for Enhanced print_mdd -----------------

def _sanitize_basename(name: str) -> str:
    """Return filesystem-safe base name (without extension)."""
    return ''.join(c for c in name if c.isalnum() or c in ('_', '-', ' ')).rstrip()

def _derive_folder_and_filename(output_path: str) -> (Path, str):
    """From requested output_path (which may or may not end with .MDD) produce:
    - folder path (without .MDD)
    - final mdd json filename (with .MDD)
    Rules: user passes /some/dir/Name.MDD or /some/dir/Name -> create /some/dir/Name/Name.MDD
    """
    raw = Path(output_path)
    # Remove .MDD/.mdd if present for folder creation
    stem = raw.name
    if stem.lower().endswith('.mdd'):
        stem = stem[: -4]
    safe_stem = _sanitize_basename(stem) or 'Standalone_MDD'
    folder = (raw.parent / safe_stem).resolve()
    filename = safe_stem + '.MDD'
    return folder, filename

def _collect_file_nodes(canvas_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [n for n in canvas_data.get('nodes', []) if n.get('type') == 'file' and 'file' in n]

def _is_canvas_reference(path_str: str) -> bool:
    return path_str.lower().endswith('.canvas')

def _copy_binary(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def _write_placeholder(dst: Path, reason: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    placeholder_text = (
        f"PLACEHOLDER FILE\nOriginal referenced file missing or unreadable.\nReason: {reason}\n"
        f"This placeholder inserted by print_mdd standalone export to preserve structure."
    )
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(placeholder_text)

def _export_canvas_recursive(parser: CanvasParser, canvas_filename: str, target_root: Path, docs_folder: Path, visited: Set[str]):
    """Recursively export a canvas file and its referenced files/MDDs.
    Returns relative path to the produced .MDD file inside target_root.
    Structure: each nested canvas gets its own subfolder under docs_folder with same fractal pattern.
    """
    # Avoid cycles
    norm_key = canvas_filename.lower()
    if norm_key in visited:
        return None
    visited.add(norm_key)

    # Parse canvas
    data = parser.parse_canvas_auto(canvas_filename)

    # Prepare current folder for this canvas inside docs (fractal)
    base_name = Path(canvas_filename).name
    base_no_ext = base_name[:-7] if base_name.lower().endswith('.canvas') else base_name
    safe_folder_name = _sanitize_basename(base_no_ext) or 'Nested'
    current_folder = docs_folder / safe_folder_name
    current_folder.mkdir(parents=True, exist_ok=True)

    # File copy handling (flat inside this current_folder/mdd_docs?)
    # For nested canvases we still want a docs subfolder for their own files to disambiguate.
    current_docs_sub = current_folder / 'mdd_docs'
    current_docs_sub.mkdir(parents=True, exist_ok=True)

    file_nodes = _collect_file_nodes(data)

    for node in file_nodes:
        original_path = node.get('file')
        if not original_path:
            continue
        # If this file node is itself a canvas reference -> recurse
        if _is_canvas_reference(original_path):
            nested_rel = _export_canvas_recursive(parser, original_path, current_folder, current_docs_sub, visited)
            if nested_rel:
                # Link the node to the nested folder's top-level MDD file
                node['file'] = str(Path('mdd_docs') / Path(nested_rel).as_posix())
            continue
        # Normal file copy
        vault_file = parser.vault_root / original_path
        # Destination: place flatly into current_docs_sub with collision handling
        dest_name = Path(original_path).name
        dest_path = current_docs_sub / dest_name
        counter = 1
        while dest_path.exists():
            # Avoid overwriting different source with same filename
            if dest_path.stat().st_size == vault_file.stat().st_size if vault_file.exists() else False:
                break
            dest_path = current_docs_sub / f"{dest_name.rsplit('.',1)[0]}_{counter}.{dest_name.rsplit('.',1)[1]}" if '.' in dest_name else current_docs_sub / f"{dest_name}_{counter}"
            counter += 1
        try:
            if vault_file.exists() and vault_file.is_file():
                # Binary vs text agnostic copy
                _copy_binary(vault_file, dest_path)
                node['file'] = str(Path('mdd_docs') / dest_path.name)
            else:
                _write_placeholder(dest_path, f"File not found: {original_path}")
                node['file'] = str(Path('mdd_docs') / dest_path.name)
        except Exception as e:
            placeholder = current_docs_sub / f"placeholder_{dest_name}"
            _write_placeholder(placeholder, f"Error copying file: {e}")
            node['file'] = str(Path('mdd_docs') / placeholder.name)

    # Save this canvas' MDD json inside its folder
    mdd_filename = safe_folder_name + '.MDD'
    mdd_path = current_folder / mdd_filename
    with open(mdd_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Return relative path (relative to current_folder parent = docs_folder for nested, or target_root for top-level?)
    return mdd_path.relative_to(current_folder) if current_folder != target_root else mdd_filename

# ---------------------------------------------------------------------------

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
            description="Parse modular documentation from Obsidian Canvas file and save it as standalone folder: <Name>/<Name>.MDD plus mdd_docs with all referenced files (recursive for nested canvases).",
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
                        "description": "Base path (file or folder). Tool will create folder <Name> and inside file <Name>.MDD plus mdd_docs. Passing either /path/Name or /path/Name.MDD is acceptable."
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
        
        try:
            parser = CanvasParser(vault_path)
            target_folder, top_filename = _derive_folder_and_filename(output_path)
            target_folder.mkdir(parents=True, exist_ok=True)
            docs_folder = target_folder / 'mdd_docs'
            docs_folder.mkdir(parents=True, exist_ok=True)

            visited: Set[str] = set()

            # Export top-level canvas recursively but store its data at top folder (not inside mdd_docs like nested ones)
            top_data = parser.parse_canvas_auto(canvas_file)
            file_nodes = _collect_file_nodes(top_data)

            # Process top-level file nodes (similar to recursive but not fractal folder yet)
            for node in file_nodes:
                original_path = node.get('file')
                if not original_path:
                    continue
                if _is_canvas_reference(original_path):
                    # Recurse: create subfolder in docs for nested canvas
                    nested_rel = _export_canvas_recursive(parser, original_path, target_folder, docs_folder, visited)
                    if nested_rel:
                        node['file'] = str(Path('mdd_docs') / Path(nested_rel).as_posix())
                    continue
                vault_file = parser.vault_root / original_path
                dest_name = Path(original_path).name
                dest_path = docs_folder / dest_name
                counter = 1
                while dest_path.exists():
                    if vault_file.exists() and dest_path.stat().st_size == vault_file.stat().st_size:
                        break
                    dest_path = docs_folder / (f"{dest_name.rsplit('.',1)[0]}_{counter}.{dest_name.rsplit('.',1)[1]}" if '.' in dest_name else f"{dest_name}_{counter}")
                    counter += 1
                try:
                    if vault_file.exists() and vault_file.is_file():
                        _copy_binary(vault_file, dest_path)
                        node['file'] = str(Path('mdd_docs') / dest_path.name)
                    else:
                        _write_placeholder(dest_path, f"File not found: {original_path}")
                        node['file'] = str(Path('mdd_docs') / dest_path.name)
                except Exception as e:
                    placeholder = docs_folder / f"placeholder_{dest_name}"
                    _write_placeholder(placeholder, f"Error copying file: {e}")
                    node['file'] = str(Path('mdd_docs') / placeholder.name)

            # Mark top canvas visited AFTER processing to avoid re-entry if self-referential
            visited.add(canvas_file.lower())

            # Save top-level MDD JSON
            top_mdd_path = target_folder / top_filename
            with open(top_mdd_path, 'w', encoding='utf-8') as f:
                json.dump(top_data, f, indent=2, ensure_ascii=False)

            return [TextContent(
                type="text",
                text=f"Standalone MDD exported to folder: {target_folder} (root file: {top_filename})"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error processing standalone MDD export: {str(e)}"
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
