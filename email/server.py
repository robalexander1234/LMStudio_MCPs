import subprocess
import json
import sys

def send_email(to, subject, body):
    ps_command = f'''
    $smtp = New-Object System.Net.Mail.SmtpClient('smtp.gmail.com', 587)
    $smtp.EnableSsl = $true
    $smtp.Credentials = New-Object System.Net.NetworkCredential('myname@gmail.com', 'api key')
    $smtp.Send('myname@gmail.com', '{to}', '{subject}', '{body}')
    '''
    result = subprocess.run(['powershell', '-Command', ps_command], capture_output=True, text=True)
    if result.returncode == 0:
        return "Email sent successfully"
    else:
        return f"Error: {result.stderr}"

# Simple MCP server loop
while True:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        request = json.loads(line)
        if request.get("method") == "tools/call":
            args = request["params"]["arguments"]
            result = send_email(args["to"], args["subject"], args["body"])
            response = {"jsonrpc": "2.0", "id": request["id"], "result": {"content": [{"type": "text", "text": result}]}}
        elif request.get("method") == "tools/list":
            response = {"jsonrpc": "2.0", "id": request["id"], "result": {"tools": [{"name": "send_email", "description": "Send an email", "inputSchema": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}}]}}
        elif request.get("method") == "initialize":
            response = {"jsonrpc": "2.0", "id": request["id"], "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "email-server", "version": "1.0.0"}}}
        else:
            response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}
        print(json.dumps(response), flush=True)
    except:
        pass