import json
import sys
from datetime import datetime
import pytz

def get_datetime():
    tz = pytz.timezone("US/Central")  # Change to your timezone
    now = datetime.now(tz)
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p %Z")

# Simple MCP server loop
while True:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        request = json.loads(line)
        if request.get("method") == "tools/call":
            result = get_datetime()
            response = {"jsonrpc": "2.0", "id": request["id"], "result": {"content": [{"type": "text", "text": result}]}}
        elif request.get("method") == "tools/list":
            response = {"jsonrpc": "2.0", "id": request["id"], "result": {"tools": [{"name": "get_datetime", "description": "Get current date and time", "inputSchema": {"type": "object", "properties": {}, "required": []}}]}}
        elif request.get("method") == "initialize":
            response = {"jsonrpc": "2.0", "id": request["id"], "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "datetime-server", "version": "1.0.0"}}}
        else:
            response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}
        print(json.dumps(response), flush=True)
    except:
        pass
