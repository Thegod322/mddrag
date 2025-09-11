#!/usr/bin/env python3
"""
Debug script to test MCP server connection and tool availability
This simulates what Claude Desktop should see when connecting to the server
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import time

def test_server_directly():
    """Test the server by running it and sending MCP protocol messages"""
    print("🔍 Testing MCP Server Direct Connection...")
    print("=" * 60)
    
    try:
        # Start the server process
        server_path = Path(__file__).parent / "run_server.py"
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent
        )
        
        # Send MCP initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send tools/list request
        list_tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        # Send messages to server
        messages = [
            json.dumps(init_message) + "\n",
            json.dumps(list_tools_message) + "\n"
        ]
        
        print("📤 Sending messages to server...")
        for msg in messages:
            process.stdin.write(msg)
            process.stdin.flush()
            print(f"   Sent: {msg.strip()}")
        
        # Give server time to respond
        time.sleep(2)
        
        # Read responses
        print("\n📥 Server responses:")
        try:
            # Try to read with timeout
            stdout_data, stderr_data = process.communicate(timeout=5)
            
            if stdout_data:
                print("STDOUT:")
                for line in stdout_data.strip().split('\n'):
                    if line.strip():
                        try:
                            parsed = json.loads(line)
                            print(f"   {json.dumps(parsed, indent=2)}")
                            
                            # Check if this is tools/list response
                            if parsed.get('id') == 2 and 'result' in parsed:
                                tools = parsed['result'].get('tools', [])
                                print(f"\n🛠️  Found {len(tools)} tools:")
                                for tool in tools:
                                    print(f"   - {tool.get('name', 'Unknown')}")
                                    
                                print_mdd_found = any(t.get('name') == 'print_mdd' for t in tools)
                                print(f"\n✅ print_mdd found: {print_mdd_found}")
                                
                        except json.JSONDecodeError:
                            print(f"   Raw: {line}")
            
            if stderr_data:
                print("\nSTDERR:")
                print(stderr_data)
                
        except subprocess.TimeoutExpired:
            print("⏱️  Server response timeout")
            process.kill()
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        import traceback
        traceback.print_exc()

def check_config_syntax():
    """Check claude_desktop_config.json syntax"""
    print("\n🔍 Checking Claude Desktop Config...")
    print("=" * 60)
    
    config_paths = [
        Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json",  # Windows
        Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",  # macOS
        Path.home() / ".config/Claude/claude_desktop_config.json"  # Linux
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            print(f"📁 Found config: {config_path}")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                print("✅ Config syntax is valid JSON")
                
                # Check for MDDRAG server
                mcp_servers = config.get('mcpServers', {})
                if 'MDDRAG' in mcp_servers:
                    mddrag_config = mcp_servers['MDDRAG']
                    print(f"✅ Found MDDRAG server config:")
                    print(f"   Command: {mddrag_config.get('command')}")
                    print(f"   Args: {mddrag_config.get('args')}")
                    
                    # Check if the server file exists
                    if 'args' in mddrag_config and mddrag_config['args']:
                        server_path = Path(mddrag_config['args'][0])
                        if server_path.exists():
                            print(f"✅ Server file exists: {server_path}")
                        else:
                            print(f"❌ Server file NOT found: {server_path}")
                else:
                    print("❌ MDDRAG server not found in config")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Config JSON syntax error: {e}")
            except Exception as e:
                print(f"❌ Error reading config: {e}")
            break
    else:
        print("❌ No Claude Desktop config found")

def main():
    """Main diagnostic function"""
    print("🚀 MCP Server Diagnostic Tool")
    print("This tool helps diagnose why print_mdd tool is not visible in Claude Desktop")
    print("=" * 80)
    
    check_config_syntax()
    test_server_directly()
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS:")
    print("1. Completely close Claude Desktop (check Task Manager)")
    print("2. Wait 10 seconds")
    print("3. Restart Claude Desktop")
    print("4. Check MCP connection status in Claude Desktop")
    print("5. If still not working, try restarting your computer")

if __name__ == "__main__":
    main()
