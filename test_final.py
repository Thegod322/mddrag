#!/usr/bin/env python3

import sys
from pathlib import Path

src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_everything():
    print("Final Documentation RAG Test")
    print("=" * 40)
    
    success = True
    
    # Test Canvas parser
    try:
        from documentation_rag.canvas_parser import CanvasParser
        print("OK: Canvas parser imported")
    except Exception as e:
        print(f"ERROR: Canvas parser failed: {e}")
        success = False
    
    # Test simple server
    try:
        from documentation_rag.server_simple import SimpleSearchEngine, server
        print("OK: Simple server imported")
        print(f"OK: MCP server name: {server.name}")
    except Exception as e:
        print(f"ERROR: Simple server failed: {e}")
        success = False
    
    # Test MCP imports
    try:
        from mcp.server import Server
        from mcp.types import Tool, TextContent
        print("OK: MCP imports working")
    except Exception as e:
        print(f"ERROR: MCP imports failed: {e}")
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("SUCCESS! Your MCP server is ready!")
        print("\n1. Add this to your Claude Desktop config:")
        print('   "documentation-rag": {')
        print('     "command": "python",')
        print(f'     "args": ["{Path(__file__).parent / "run_server_simple.py"}"],')
        print(f'     "cwd": "{Path(__file__).parent}"')
        print('   }')
        print("\n2. Restart Claude Desktop")
        print("3. Try asking Claude to parse your Canvas files!")
        print("\nAvailable tools:")
        print("- get_modular_documentation: Parse Canvas files")
        print("- get_file_content: Read vault files")
        print("- search_documentation: Search with text matching")
    else:
        print("FAILED: Some components have issues")
    
    return success

if __name__ == "__main__":
    test_everything()
