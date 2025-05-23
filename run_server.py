#!/usr/bin/env python3
"""
Launcher script for Documentation RAG MCP Server

This script can be used to run the MCP server directly for testing
or as part of Claude Desktop configuration.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the server
from documentation_rag.server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
