#!/usr/bin/env python3

import sys
from pathlib import Path

src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from documentation_rag.server_simple import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
