#!/usr/bin/env python3
"""
Launcher for lightweight Documentation RAG MCP Server
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the lightweight server
from documentation_rag.server_light import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
