#!/usr/bin/env python3
"""
Test script to check which tools are returned by the MCP server
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from documentation_rag.server import handle_list_tools

async def test_tools_list():
    """Test the list of tools returned by the server"""
    print("Testing MCP Server Tools List...")
    print("=" * 50)
    
    try:
        # Get the list of tools from the server
        tools = await handle_list_tools()
        
        print(f"Total tools found: {len(tools)}")
        print()
        
        for i, tool in enumerate(tools, 1):
            print(f"{i}. Tool Name: {tool.name}")
            print(f"   Description: {tool.description}")
            print(f"   Required params: {tool.inputSchema.get('required', [])}")
            print("-" * 40)
            
        # Check specifically for print_mdd
        print("\nSpecific check for print_mdd:")
        print_mdd_found = any(tool.name == "print_mdd" for tool in tools)
        print(f"print_mdd found: {print_mdd_found}")
        
        if print_mdd_found:
            print_mdd_tool = next(tool for tool in tools if tool.name == "print_mdd")
            print(f"print_mdd description: {print_mdd_tool.description}")
            print(f"print_mdd schema: {json.dumps(print_mdd_tool.inputSchema, indent=2)}")
        
    except Exception as e:
        print(f"Error testing tools list: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tools_list())
