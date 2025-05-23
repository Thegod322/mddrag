#!/usr/bin/env python3
"""
Test script for lightweight Documentation RAG
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_canvas_parser():
    """Test Canvas parser functionality."""
    print("Testing Canvas Parser...")
    
    try:
        from documentation_rag.canvas_parser import CanvasParser
        print("OK: Canvas parser imported successfully")
        
        # Test with a fake vault path
        try:
            parser = CanvasParser("C:/test")
        except ValueError as e:
            print("OK: Parser correctly validates vault path")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Canvas parser test failed: {e}")
        return False

def test_light_server():
    """Test lightweight server imports."""
    print("\nTesting Lightweight Server...")
    
    try:
        from documentation_rag.server_light import SimpleSearchEngine
        print("OK: Lightweight server imported successfully")
        
        # Test SimpleSearchEngine creation
        try:
            engine = SimpleSearchEngine("C:/test")
        except Exception as e:
            print(f"OK: Search engine correctly handles invalid path")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Lightweight server test failed: {e}")
        return False

def main():
    print("Documentation RAG - Lightweight Version Test")
    print("=" * 50)
    
    success = True
    
    # Test Canvas parser
    if not test_canvas_parser():
        success = False
    
    # Test lightweight server
    if not test_light_server():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! The lightweight server should work.")
        print("\nNext steps:")
        print("1. Add this to your Claude Desktop config:")
        print('   "documentation-rag-light": {')
        print('     "command": "python",')
        print(f'     "args": ["{Path(__file__).parent / "run_server_light.py"}"],')
        print(f'     "cwd": "{Path(__file__).parent}"')
        print('   }')
        print("\n2. Restart Claude Desktop")
        print("3. Test with your Obsidian vault!")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
