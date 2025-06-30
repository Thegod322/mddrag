#!/usr/bin/env python3
"""
Launcher for Documentation RAG MCP Server v2 (with external docs support)
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the v2 server
from documentation_rag.server_v2 import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
