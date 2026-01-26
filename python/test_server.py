#!/usr/bin/env python3
"""
Test script for Python MCP Server
Run this to verify your installation works correctly.
"""

import subprocess
import json
import sys
import os

def send_message(proc, message):
    """Send a JSON-RPC message and get response."""
    msg_str = json.dumps(message) + "\n"
    proc.stdin.write(msg_str)
    proc.stdin.flush()
    response = proc.stdout.readline()
    return json.loads(response) if response else None

def main():
    print("=" * 60)
    print("Python MCP Server Test")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "python_mcp_server.py")
    
    # Start the server
    print("\n1. Starting MCP server...")
    try:
        proc = subprocess.Popen(
            [sys.executable, server_path],
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
    print("\n2. Initializing...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    })
    if response and "result" in response:
        print(f"   OK - Server: {response['result']['serverInfo']['name']}")
    else:
        print(f"   FAILED: {response}")
        return 1
    
    # Send initialized notification
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }) + "\n")
    proc.stdin.flush()
    
    # List tools
    print("\n3. Listing tools...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    })
    if response and "result" in response:
        tools = response["result"]["tools"]
        print(f"   OK - Found {len(tools)} tools:")
        for tool in tools:
            print(f"      - {tool['name']}")
    else:
        print(f"   FAILED: {response}")
        return 1
    
    # Test python_execute
    print("\n4. Testing python_execute (2 + 2)...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "python_execute",
            "arguments": {"code": "2 + 2"}
        }
    })
    if response and "result" in response:
        result = json.loads(response["result"]["content"][0]["text"])
        print(f"   OK - Result: {result.get('result', 'None')}")
    else:
        print(f"   FAILED: {response}")
        return 1
    
    # Test variable persistence
    print("\n5. Testing variable persistence...")
    send_message(proc, {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "python_execute",
            "arguments": {"code": "x = 42"}
        }
    })
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "python_get_variable",
            "arguments": {"name": "x"}
        }
    })
    if response and "result" in response:
        result = json.loads(response["result"]["content"][0]["text"])
        if result.get("value") == "42":
            print(f"   OK - Variable x = {result['value']}")
        else:
            print(f"   FAILED: Expected 42, got {result}")
            return 1
    else:
        print(f"   FAILED: {response}")
        return 1
    
    # Test list comprehension
    print("\n6. Testing list comprehension...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "python_execute",
            "arguments": {"code": "[i**2 for i in range(5)]"}
        }
    })
    if response and "result" in response:
        result = json.loads(response["result"]["content"][0]["text"])
        print(f"   OK - Result: {result.get('result', 'None')}")
    else:
        print(f"   FAILED: {response}")
        return 1
    
    # Test import
    print("\n7. Testing import (math)...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "python_execute",
            "arguments": {"code": "import math; math.pi"}
        }
    })
    if response and "result" in response:
        result = json.loads(response["result"]["content"][0]["text"])
        print(f"   OK - math.pi = {result.get('result', 'None')}")
    else:
        print(f"   FAILED: {response}")
        return 1
    
    # Test list_variables
    print("\n8. Testing list_variables...")
    response = send_message(proc, {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "python_list_variables",
            "arguments": {}
        }
    })
    if response and "result" in response:
        result = json.loads(response["result"]["content"][0]["text"])
        print(f"   OK - Found {len(result)} variables")
    else:
        print(f"   FAILED: {response}")
        return 1
    
    # Cleanup
    proc.terminate()
    proc.wait()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour Python MCP server is ready to use with LMStudio.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
