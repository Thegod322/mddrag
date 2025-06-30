# Documentation RAG MCP Server

An MCP (Model Context Protocol) server that implements **CRAG (Canvas-Relational Augmented Generation)** - a novel approach to RAG that uses visual Canvas structures with explicit node relationships, rather than traditional text chunking.

Provides intelligent access to your documentation through three focused tools:

1. **MDD Canvas Parsing** - Parse and understand Obsidian Canvas-based Modular Development Documentation
2. **File Content Access** - Retrieve content from files referenced in your documentation  
3. **Semantic Search** - Search across external documentation libraries using AI

## ✨ Key Features

- **CRAG Architecture**: Visual knowledge mapping through Canvas with explicit relationships
- **Smart Canvas Parsing**: Understands Obsidian Canvas files with automatic recursive search
- **MDD Support**: Optimized for Modular Development Documentation workflows
- **Flexible File Access**: Read any file from your vault with simple file name specification
- **External Documentation Search**: Search across pre-indexed libraries, frameworks, and tools
- **Simple UX**: Just specify vault path and file names - the server handles the rest

## 🚀 Quick Installation

**New users**: See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed step-by-step instructions.

**Experienced users**: 
1. Install dependencies: `pip install -r requirements.txt`
2. Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "documentation-rag": {
      "command": "python",
      "args": ["C:\\path\\to\\your\\run_server.py"]
    }
  }
}
```
3. Restart Claude Desktop

## 🛠️ Available Tools

The server provides exactly **3 focused tools**:

### 1. `d94_get_modular_documentation`
Parse and understand Obsidian Canvas files (.canvas) with CRAG and MDD support.

**Parameters:**
- `vault_path`: Path to your Obsidian vault
- `canvas_file`: Name of the Canvas file (e.g., "MyProject.canvas")

**CRAG Features**: Extracts not just content, but visual relationships and node positioning for contextual understanding.

**New UX**: Just specify the file name! The server automatically searches your entire vault recursively to find the Canvas file.

### 2. `d94_get_file_content`  
Read content from any file referenced in your documentation.

**Parameters:**
- `vault_path`: Path to your Obsidian vault
- `file_path`: Relative path to the file from vault root

### 3. `d94_search_documentation`
Semantic search across pre-indexed external documentation.

**Parameters:**
- `query`: Your search query in natural language
- `limit`: Maximum number of results (default: 5)

**Pre-indexed libraries**: Godot, and others (expandable)

## 💡 Example Usage

### Parse Your Canvas Documentation
```
Parse the canvas file "ProjectDocs.canvas" from my vault at "C:/MyVault"
```
The server automatically finds the Canvas file anywhere in your vault structure.

### Read Documentation Files  
```
Get the content of "API-Reference.md" from my vault at "C:/MyVault"
```

### Search External Documentation
```
Search for "CharacterBody3D movement" in the documentation
```

## 🔧 Technical Details

### Architecture
- **CRAG Implementation**: Canvas-Relational Augmented Generation with visual knowledge mapping
- **Focused Design**: Only 3 essential tools for maximum clarity
- **MDD Integration**: Specialized support for Modular Development Documentation
- **Recursive Search**: Automatically finds files in complex vault structures
- **Persistent Storage**: External documentation indexed once, available always

### Storage Location
External documentation is stored in:
- Windows: `C:\Users\[Username]\.documentation_rag\`
- macOS/Linux: `~/.documentation_rag/`

Contains:
- `chroma_db/` - Vector database for semantic search
- `docs_metadata.json` - Documentation metadata

## 🧪 Testing

Test the core functionality:
```bash
python test_mcp_client.py
```

Test specific components:
```bash
# Test Canvas parsing
python test_rag.py

# Test external documentation search  
python test_external_docs.py
```

## 🔍 How It Works

1. **CRAG Canvas Parsing**: Uses specialized parser to understand Canvas node relationships, visual positioning, and MDD structure
2. **Relational Context**: Maintains explicit relationships between documentation nodes rather than treating them as isolated chunks
3. **Recursive File Discovery**: Automatically finds files throughout complex vault hierarchies  
4. **Semantic Search**: Employs sentence-transformers for intelligent similarity-based search
5. **Persistent Storage**: ChromaDB ensures external documentation remains available across sessions

**CRAG vs Traditional RAG**: Instead of chunking text randomly, CRAG preserves the author's intended knowledge structure through visual Canvas relationships.

## 🛠️ Troubleshooting

### Common Issues

**"No MCP tools available"**
- Verify Python path in Claude Desktop config
- Ensure all dependencies are installed
- Restart Claude Desktop completely

**"Canvas file not found"**  
- Check vault path is correct
- Ensure Canvas file has `.canvas` extension
- File will be found automatically in any subfolder

**"Search returns no results"**
- External documentation must be pre-indexed
- Check that ChromaDB has proper permissions
- Try broader search terms

### Getting Help

- **Detailed Setup**: See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Test Files**: Run test scripts to diagnose issues
- **Logs**: Check Claude Desktop logs for specific error messages

## 📋 System Requirements

- Python 3.8+
- Claude Desktop
- ~500MB storage for ChromaDB and embeddings
- Internet connection for initial model download

---

**Ready to enhance your documentation workflow with intelligent AI assistance!** 🚀
