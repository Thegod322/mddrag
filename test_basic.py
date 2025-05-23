#!/usr/bin/env python3
"""
Simple Canvas Parser Test - No MCP Dependencies
"""

import json
from pathlib import Path

def test_basic_functionality():
    """Test basic Canvas parsing without MCP."""
    print("Simple Canvas Parser Test")
    print("=" * 30)
    
    # Test canvas parser logic directly
    try:
        # Simple Canvas parser
        class SimpleCanvasParser:
            def __init__(self, vault_root):
                self.vault_root = Path(vault_root)
            
            def parse_canvas_file(self, canvas_path):
                full_path = self.vault_root / canvas_path
                if not full_path.exists():
                    raise FileNotFoundError(f"Canvas file not found: {canvas_path}")
                
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                nodes = data.get("nodes", [])
                edges = data.get("edges", [])
                
                return {
                    "nodes": len(nodes),
                    "edges": len(edges),
                    "canvas_path": canvas_path,
                    "status": "success"
                }
        
        # Test the parser
        parser = SimpleCanvasParser(".")
        print("OK: Simple Canvas parser created")
        
        # Test with sample data
        sample_canvas = {
            "nodes": [
                {"id": "1", "type": "text", "text": "Test Node"},
                {"id": "2", "type": "file", "file": "test.md"}
            ],
            "edges": [
                {"id": "e1", "fromNode": "1", "toNode": "2"}
            ]
        }
        
        # Write test canvas
        test_path = Path("test_canvas.json")
        with open(test_path, "w") as f:
            json.dump(sample_canvas, f)
        
        # Test parsing
        result = parser.parse_canvas_file("test_canvas.json")
        print(f"OK: Parsed test canvas - {result['nodes']} nodes, {result['edges']} edges")
        
        # Cleanup
        test_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main test function."""
    success = test_basic_functionality()
    
    print("\n" + "=" * 30)
    if success:
        print("SUCCESS: Basic functionality works!")
        print("\nYour system can handle:")
        print("- JSON parsing")
        print("- File operations") 
        print("- Canvas structure analysis")
        print("\nNext: Install proper MCP dependencies")
    else:
        print("FAILED: Basic functionality has issues")

if __name__ == "__main__":
    main()
