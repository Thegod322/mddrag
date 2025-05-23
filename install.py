#!/usr/bin/env python3
"""
Installation script for Documentation RAG MCP Server
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(cmd)}")
    if description:
        print(f"Description: {description}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is suitable."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"Error: Python 3.8+ required, but found {version.major}.{version.minor}")
        return False
    
    print(f"Python version: {version.major}.{version.minor}.{version.micro} OK")
    return True


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    
    # Core dependencies
    dependencies = [
        "mcp>=1.0.0",
        "chromadb>=0.4.0", 
        "sentence-transformers>=2.2.0",
        "pydantic>=2.0.0"
    ]
    
    for dep in dependencies:
        print(f"\nInstalling {dep}...")
        if not run_command([sys.executable, "-m", "pip", "install", dep]):
            print(f"Failed to install {dep}")
            return False
    
    return True


def install_dev_dependencies():
    """Install development dependencies."""
    print("Installing development dependencies...")
    
    dev_deps = [
        "pytest>=7.0.0",
        "black>=23.0.0",
        "mypy>=1.0.0"
    ]
    
    for dep in dev_deps:
        print(f"\nInstalling {dep}...")
        if not run_command([sys.executable, "-m", "pip", "install", dep]):
            print(f"Warning: Failed to install {dep} (optional)")
    
    return True


def install_editable():
    """Install package in editable mode."""
    print("Installing package in editable mode...")
    return run_command([sys.executable, "-m", "pip", "install", "-e", "."])


def main():
    """Main installation function."""
    print("Documentation RAG MCP Server - Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    print(f"Project directory: {project_dir}")
    
    # Upgrade pip first
    print("\nUpgrading pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install core dependencies")
        sys.exit(1)
    
    # Ask about dev dependencies
    install_dev = input("\nInstall development dependencies? (y/N): ").strip().lower()
    if install_dev == 'y':
        install_dev_dependencies()
    
    # Install in editable mode
    install_editable_mode = input("\nInstall in editable mode? (Y/n): ").strip().lower()
    if install_editable_mode != 'n':
        if not install_editable():
            print("Warning: Failed to install in editable mode")
    
    print("\n" + "=" * 50)
    print("Installation completed!")
    print("\nNext steps:")
    print("1. Test the installation: python test_rag.py")
    print("2. Add to Claude Desktop config:")
    print("   {")
    print('     "mcpServers": {')
    print('       "documentation-rag": {')
    print('         "command": "python",')
    print(f'         "args": ["-m", "documentation_rag.server"],')
    print(f'         "cwd": "{project_dir / "src"}"')
    print('       }')
    print('     }')
    print("   }")
    print("\n3. Restart Claude Desktop")


if __name__ == "__main__":
    main()
