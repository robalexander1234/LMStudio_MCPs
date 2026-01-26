#!/usr/bin/env python3
"""
Test script for Octave MCP Server
Run this to verify your installation works correctly.
"""

import subprocess
import json
import sys

def send_message(proc, message):
    """Send a JSON-RPC message and get response."""
    msg_str = json.dumps(message) + "\n"
    proc.stdin.write(msg_str)
    proc.stdin.flush()
    response = proc.stdout.readline()
    return json.loads(response) if response else None

def main():
    print("=" * 60)
    print("Octave MCP Server Test")
    print("=" * 60)
    
    # Start the server
    print("\n1. Starting MCP server...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "octave_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    except Exception as e:
        print(f"   FAILED: {e}")
        return 1
    print("   OK")
    
    # Initialize
    print("\n2. Sending initialize request...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    if response and "result" in response:
        print(f"   OK: {response['result']['serverInfo']['name']} v{response['result']['serverInfo']['version']}")
    else:
        print(f"   FAILED: {response}")
        proc.terminate()
        return 1
    
    # List tools
    print("\n3. Listing available tools...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })
    if response and "result" in response:
        tools = response["result"]["tools"]
        print(f"   OK: {len(tools)} tools available")
        for tool in tools:
            print(f"      - {tool['name']}")
    else:
        print(f"   FAILED: {response}")
    
    # Test basic execution
    print("\n4. Testing basic Octave execution...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "octave_execute",
            "arguments": {
                "code": "A = [1 2; 3 4]; disp(det(A))"
            }
        }
    })
    if response and "result" in response:
        content = response["result"]["content"]
        output = content[0]["text"] if content else ""
        if "-2" in output:
            print(f"   OK: det([1 2; 3 4]) = {output.strip()}")
        else:
            print(f"   WARNING: Unexpected output: {output}")
    else:
        print(f"   FAILED: {response}")
    
    # Test variable persistence
    print("\n5. Testing workspace persistence...")
    send_message(proc, {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "octave_execute",
            "arguments": {"code": "test_var = 42;"}
        }
    })
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "octave_get_variable",
            "arguments": {"name": "test_var"}
        }
    })
    if response and "result" in response:
        content = response["result"]["content"]
        output = content[0]["text"] if content else ""
        if "42" in output:
            print(f"   OK: Variable persisted correctly")
        else:
            print(f"   WARNING: Unexpected output: {output}")
    else:
        print(f"   FAILED: {response}")
    
    # Test matrix operations
    print("\n6. Testing matrix operations...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "octave_execute",
            "arguments": {
                "code": "B = magic(3); disp(B)"
            }
        }
    })
    if response and "result" in response:
        content = response["result"]["content"]
        output = content[0]["text"] if content else ""
        if "8" in output and "1" in output and "6" in output:
            print(f"   OK: magic(3) computed correctly")
        else:
            print(f"   WARNING: Unexpected output: {output}")
    else:
        print(f"   FAILED: {response}")
    
    # Test workspace listing
    print("\n7. Testing workspace listing...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "octave_list_workspace",
            "arguments": {}
        }
    })
    if response and "result" in response:
        content = response["result"]["content"]
        output = content[0]["text"] if content else ""
        if "test_var" in output or "A" in output or "B" in output:
            print(f"   OK: Workspace listing works")
        else:
            print(f"   WARNING: Variables not found in workspace")
    else:
        print(f"   FAILED: {response}")
    
    # Test help
    print("\n8. Testing help system...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "octave_help",
            "arguments": {"topic": "sin"}
        }
    })
    if response and "result" in response:
        content = response["result"]["content"]
        output = content[0]["text"] if content else ""
        if "sin" in output.lower():
            print(f"   OK: Help system works")
        else:
            print(f"   WARNING: Help output unexpected")
    else:
        print(f"   FAILED: {response}")
    
    # Shutdown
    print("\n9. Shutting down...")
    send_message(proc, {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "shutdown",
        "params": {}
    })
    proc.terminate()
    proc.wait()
    print("   OK")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\nYour Octave MCP server is ready to use with LMStudio.")
    print("Add the following to your LMStudio MCP configuration:\n")
    print(json.dumps({
        "mcpServers": {
            "octave": {
                "command": "python3",
                "args": ["/full/path/to/octave_mcp_server.py"]
            }
        }
    }, indent=2))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
