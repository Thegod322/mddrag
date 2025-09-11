#!/usr/bin/env python3
"""
Test script to check if print_mdd tool works correctly
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from documentation_rag.server import handle_call_tool

async def test_print_mdd():
    """Test the print_mdd tool functionality"""
    print("Testing print_mdd tool...")
    print("=" * 50)
    
    # Test arguments - using mock data since we don't know your actual canvas files
    test_args = {
        "canvas_file": "test.canvas",  # This will likely fail, but let's see the error message
        "output_path": "./test_output.MDD"
    }
    
    try:
        # Call the print_mdd tool
        result = await handle_call_tool("print_mdd", test_args)
        
        print(f"Result type: {type(result)}")
        print(f"Number of results: {len(result)}")
        
        for i, content in enumerate(result):
            print(f"Result {i+1}:")
            print(f"  Type: {content.type}")
            print(f"  Text: {content.text[:200]}...")  # First 200 chars
            print("-" * 40)
            
    except Exception as e:
        print(f"Error testing print_mdd: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_print_mdd())
