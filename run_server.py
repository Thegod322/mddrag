#!/usr/bin/env python3
"""
Launcher script for Documentation RAG MCP Server (Unified)

This script launches the unified MCP server that supports both:
- Obsidian Canvas-based modular documentation (MDD method)  
- External documentation libraries indexed in ChromaDB

This is the main entry point for the Documentation RAG MCP Server.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the unified server
from documentation_rag.server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
