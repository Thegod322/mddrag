# Archive Directory

This directory contains the old server implementations that were replaced during the refactoring process.

## Archived Files:

### `run_server_v2.py`
- Old launcher for the v2 server
- Replaced by the unified `run_server.py`

### `server_v1.py` (originally `server.py`)
- Original server implementation
- Supported only Obsidian Canvas functionality
- Tools: get_modular_documentation, get_file_content, search_documentation, index_documentation

### `server_v2.py`
- Second server implementation
- Added external documentation support via ChromaDB
- Had architectural issues with undeclared tools

## Migration Summary:
All functionality from both servers has been merged into the new unified `server.py` which provides:
- Complete Obsidian Canvas/MDD support (from v1)
- External documentation/ChromaDB support (from v2)
- Proper tool declaration architecture
- Clear separation between project docs (Obsidian) and library docs (ChromaDB)

These files are kept for reference only and should not be used.
