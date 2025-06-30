#!/usr/bin/env python3
"""
Unified Launcher for Documentation RAG MCP Server

This script launches the unified MCP server that supports both:
- Obsidian Canvas-based modular documentation (MDD method)
- External documentation libraries indexed in ChromaDB

Usage:
    python run_server.py
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the unified server
from documentation_rag.server_unified import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
