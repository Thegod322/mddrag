#!/usr/bin/env python3
"""
MCP Client Test Script

This script tests the Documentation RAG MCP server using the MCP protocol.
It connects to the server and tests all available tools.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


async def test_mcp_server():
    """Test the MCP server by spawning a subprocess and communicating via stdio."""
    
    print("Documentation RAG MCP Server Test")
    print("=" * 40)
    
    # Get vault path from user
    vault_path = input("Enter path to your Obsidian vault: ").strip()
    if not vault_path or not Path(vault_path).exists():
        print("Invalid vault path")
        return
    
    # Start the MCP server process
    server_script = Path(__file__).parent / "run_server.py"
    print(f"Starting MCP server: {server_script}")
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        print("MCP server started, testing communication...")
        
        # Send initialization message
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialization...")
        process.stdin.write(json.dumps(init_msg) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                print(f"Server initialized: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
            except json.JSONDecodeError:
                print(f"Invalid JSON response: {response_line}")
        
        # Send initialized notification
        initialized_msg = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write(json.dumps(initialized_msg) + "\n")
        process.stdin.flush()
        
        # List available tools
        list_tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        print("\nListing available tools...")
        process.stdin.write(json.dumps(list_tools_msg) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                tools = response.get("result", {}).get("tools", [])
                print(f"Available tools ({len(tools)}):")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
            except json.JSONDecodeError:
                print(f"Invalid JSON response: {response_line}")
        
        # Test get_modular_documentation if there are Canvas files
        canvas_files = list(Path(vault_path).glob("**/*.canvas"))
        if canvas_files:
            canvas_file = canvas_files[0].relative_to(Path(vault_path))
            print(f"\nTesting get_modular_documentation with {canvas_file}...")
            
            tool_call_msg = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_modular_documentation",
                    "arguments": {
                        "vault_path": vault_path,
                        "canvas_file": str(canvas_file)
                    }
                }
            }
            
            process.stdin.write(json.dumps(tool_call_msg) + "\n")
            process.stdin.flush()
            
            response_line = process.stdout.readline()
            if response_line:
                try:
                    response = json.loads(response_line.strip())
                    content = response.get("result", {}).get("content", [])
                    if content and content[0].get("text"):
                        canvas_data = json.loads(content[0]["text"])
                        print(f"OK Canvas parsed successfully!")
                        print(f"  Nodes: {canvas_data.get('metadata', {}).get('total_nodes', 0)}")
                        print(f"  Edges: {canvas_data.get('metadata', {}).get('total_edges', 0)}")
                    else:
                        print("ERROR No content returned")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"ERROR Error parsing response: {e}")
        else:
            print("No Canvas files found in vault")
        
        # Test file reading
        md_files = list(Path(vault_path).glob("**/*.md"))
        if md_files:
            md_file = md_files[0].relative_to(Path(vault_path))
            print(f"\nTesting get_file_content with {md_file}...")
            
            tool_call_msg = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "get_file_content",
                    "arguments": {
                        "vault_path": vault_path,
                        "file_path": str(md_file)
                    }
                }
            }
            
            process.stdin.write(json.dumps(tool_call_msg) + "\n")
            process.stdin.flush()
            
            response_line = process.stdout.readline()
            if response_line:
                try:
                    response = json.loads(response_line.strip())
                    content = response.get("result", {}).get("content", [])
                    if content and content[0].get("text"):
                        file_content = content[0]["text"]
                        print(f"OK File read successfully!")
                        print(f"  Length: {len(file_content)} characters")
                        print(f"  Preview: {file_content[:100]}...")
                    else:
                        print("ERROR No content returned")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"ERROR Error parsing response: {e}")
        
        print("\n" + "=" * 40)
        print("MCP server test completed!")
        
    except Exception as e:
        print(f"Error testing MCP server: {e}")
    
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()


def test_direct_import():
    """Test by importing the modules directly (simpler test)."""
    print("\nDirect Import Test")
    print("=" * 20)
    
    try:
        from documentation_rag.canvas_parser import CanvasParser
        from documentation_rag.rag_engine import RAGEngine
        print("OK Modules imported successfully")
        
        vault_path = input("Enter path to your Obsidian vault: ").strip()
        if not vault_path or not Path(vault_path).exists():
            print("Invalid vault path")
            return
        
        # Test Canvas parser
        parser = CanvasParser(vault_path)
        canvas_files = list(Path(vault_path).glob("**/*.canvas"))
        
        if canvas_files:
            canvas_file = canvas_files[0].relative_to(Path(vault_path))
            print(f"Testing Canvas parser with {canvas_file}...")
            
            canvas_data = parser.parse_canvas_file(str(canvas_file))
            print(f"OK Canvas parsed successfully!")
            print(f"  Nodes: {canvas_data.get('metadata', {}).get('total_nodes', 0)}")
            print(f"  Edges: {canvas_data.get('metadata', {}).get('total_edges', 0)}")
        
        print("OK Direct import test completed!")
        
    except Exception as e:
        print(f"ERROR Error in direct import test: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("Choose test method:")
    print("1. Test as MCP server (full protocol test)")
    print("2. Test direct import (simpler test)")
    
    choice = input("Choice (1 or 2): ").strip()
    
    if choice == "1":
        await test_mcp_server()
    elif choice == "2":
        test_direct_import()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
