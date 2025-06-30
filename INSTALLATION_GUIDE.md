# 📋 Complete Installation Guide - Documentation RAG MCP Server

This guide will walk you through setting up the Documentation RAG MCP Server from scratch, step by step. No prior experience with MCP servers required!

## 🎯 What You'll Get

After following this guide, you'll have:
- ✅ A working MCP server implementing **CRAG (Canvas-Relational Augmented Generation)**
- ✅ Visual knowledge mapping through Canvas with explicit node relationships  
- ✅ Full support for MDD (Modular Development Documentation) workflows
- ✅ Semantic search across external documentation (libraries, frameworks, tools)
- ✅ Integration with Claude Desktop for intelligent document assistance

**CRAG vs Traditional RAG**: Unlike traditional text chunking, CRAG preserves your intended knowledge structure through visual Canvas relationships.

## 📋 Prerequisites

### Required Software
1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **Important**: During installation, check "Add Python to PATH"

2. **Claude Desktop**
   - Download from: https://claude.ai/download
   - Create an account if you don't have one

3. **Git** (optional, for cloning the repository)
   - Download from: https://git-scm.com/downloads

## 🚀 Step-by-Step Installation

### Step 1: Download the Project

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/your-username/documentation-rag-mcp.git
cd documentation-rag-mcp
```

**Option B: Download ZIP**
1. Download the project as a ZIP file
2. Extract it to a folder like `C:\ClaudeHub\MCP\DocumentationRag`
3. Open Command Prompt or PowerShell in that folder

### Step 2: Install Python Dependencies

Open Command Prompt or PowerShell in the project folder and run:

```bash
pip install -r requirements.txt
```

**If you get an error**, try:
```bash
python -m pip install -r requirements.txt
```

**Expected output**: You should see packages being installed, including:
- `mcp`
- `chromadb`
- `sentence-transformers`
- And others...

### Step 3: Test the Installation

Run a quick test to make sure everything is installed correctly:

```bash
python test_mcp_client.py
```

**Expected output**: 
```
✅ MCP Server test passed!
✅ All tools are available and working
```

### Step 4: Configure Claude Desktop

This is the most important step! You need to tell Claude Desktop where to find your MCP server.

#### Find Your Configuration File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```
(Type this path in File Explorer address bar)

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

#### Edit the Configuration

1. Open the `claude_desktop_config.json` file in a text editor
2. If the file doesn't exist, create it
3. Add this configuration (replace the path with your actual project path):

```json
{
  "mcpServers": {
    "documentation-rag": {
      "command": "python",
      "args": ["C:\\ClaudeHub\\MCP\\DocumentationRag\\run_server.py"]
    }
  }
}
```

**⚠️ Important Notes:**
- Use **double backslashes** (`\\`) in Windows paths
- Use **forward slashes** (`/`) in macOS/Linux paths
- Replace `C:\\ClaudeHub\\MCP\\DocumentationRag` with your actual project path

#### Example Configurations

**Windows Example:**
```json
{
  "mcpServers": {
    "documentation-rag": {
      "command": "python",
      "args": ["C:\\Users\\YourName\\Documents\\documentation-rag-mcp\\run_server.py"]
    }
  }
}
```

**macOS/Linux Example:**
```json
{
  "mcpServers": {
    "documentation-rag": {
      "command": "python",
      "args": ["/Users/YourName/Documents/documentation-rag-mcp/run_server.py"]
    }
  }
}
```

### Step 5: Restart Claude Desktop

1. **Completely close** Claude Desktop (check system tray/menu bar)
2. **Restart** Claude Desktop
3. Wait for it to fully load

### Step 6: Verify the Connection

1. Open a new conversation in Claude Desktop
2. Type: "What MCP tools do you have available?"
3. You should see these three tools listed:
   - `d94_get_modular_documentation`
   - `d94_get_file_content` 
   - `d94_search_documentation`

**If you don't see the tools**, check the [Troubleshooting](#-troubleshooting) section below.

## 🧪 Testing Your Setup

### Test 1: Search External Documentation

```
Search for "Character body 3D" in the documentation
```

Expected: Claude should find and return relevant documentation about 3D character bodies.

### Test 2: Parse Obsidian Canvas (if you have one)

```
Parse the canvas file "MyProject.canvas" from my vault at "C:\Users\YourName\Documents\MyVault"
```

Expected: Claude should find and parse your Canvas file, showing nodes and connections.

### Test 3: Read File Content

```
Get the content of the file "README.md" from my vault at "C:\Users\YourName\Documents\MyVault"
```

Expected: Claude should read and display the file content.

## 🛠️ Troubleshooting

### Problem: "No MCP tools available"

**Possible Solutions:**
1. **Check the path**: Make sure the path in `claude_desktop_config.json` is correct
2. **Check Python**: Run `python --version` to confirm Python is installed
3. **Check dependencies**: Run `pip list` and verify `mcp` is installed
4. **Restart Claude**: Completely close and restart Claude Desktop
5. **Check logs**: Look for error messages in Claude Desktop

### Problem: "Python command not found"

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or use the full Python path in your config:
   ```json
   {
     "mcpServers": {
       "documentation-rag": {
         "command": "C:\\Python310\\python.exe",
         "args": ["C:\\path\\to\\your\\run_server.py"]
       }
     }
   }
   ```

### Problem: "Module not found" errors

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Problem: "Permission denied" errors

**Solution:**
1. Run Command Prompt as Administrator
2. Or check that the project folder has write permissions

### Problem: "No canvas files found"

**Solution:**
1. Make sure your Canvas file has the `.canvas` extension
2. Check that the vault path is correct
3. The server searches recursively, so the file can be in any subfolder

## 🔧 Advanced Configuration

### Using Virtual Environments (Recommended)

For better dependency management:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Then update your Claude config to use the virtual environment's Python:
```json
{
  "mcpServers": {
    "documentation-rag": {
      "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\your\\run_server.py"]
    }
  }
}
```

### Custom Storage Location

By default, external documentation is stored in:
- Windows: `C:\Users\[Username]\.documentation_rag\`
- macOS/Linux: `~/.documentation_rag/`

To change this, set the environment variable `DOCUMENTATION_RAG_HOME`:
```bash
# Windows
set DOCUMENTATION_RAG_HOME=C:\MyCustomPath

# macOS/Linux
export DOCUMENTATION_RAG_HOME=/path/to/custom/location
```

## 🎉 You're Ready!

Congratulations! Your Documentation RAG MCP Server is now set up and ready to use. 

### What's Next?

1. **Load some documentation**: Ask Claude to search for topics you're interested in
2. **Parse your Canvas files**: If you use Obsidian Canvas, try parsing your documentation
3. **Explore the features**: Try different search queries and file operations

### Getting Help

- **Issues**: Check the main README.md for troubleshooting tips
- **Documentation**: Read about all available tools in the README.md
- **Examples**: Look at the test files to see example usage

---

**Happy documenting! 📚✨**
