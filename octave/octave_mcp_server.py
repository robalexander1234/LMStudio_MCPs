#!/usr/bin/env python3
"""
Octave MCP Server - Model Context Protocol server for GNU Octave
Allows LLMs (via LMStudio or other MCP clients) to execute Octave code.
"""

import json
import subprocess
import tempfile
import os
import base64
import sys
import threading
import queue
from typing import Any

# MCP Protocol Implementation
class OctaveMCPServer:
    def __init__(self):
        self.octave_process = None
        self.workspace_dir = tempfile.mkdtemp(prefix="octave_mcp_")
        self.figure_counter = 0
        self.history = []
        
    def start_octave(self):
        """Start a persistent Octave process."""
        if self.octave_process is None or self.octave_process.poll() is not None:
            self.octave_process = subprocess.Popen(
                [r"C:\Program Files\GNU Octave\Octave-10.1.0\octave-launch.exe", 
                 "--no-gui", "--interactive", "--quiet"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=self.workspace_dir
            )
            # Initialize Octave with some useful settings
            self._send_command("graphics_toolkit('gnuplot');")
            self._send_command(f"cd('{self.workspace_dir}');")
        return True
    
    def _send_command(self, command: str, timeout: float = 30.0) -> dict:
        """Send a command to Octave and get the result."""
        if self.octave_process is None:
            raise RuntimeError("Octave process not started")
        
        # Add a unique marker to detect end of output
        marker = f"__MCP_END_MARKER_{id(command)}__"
        full_command = f"{command}\ndisp('{marker}')\n"
        
        try:
            self.octave_process.stdin.write(full_command)
            self.octave_process.stdin.flush()
        except BrokenPipeError:
            return {"success": False, "error": "Octave process died", "output": ""}
        
        # Read output until we see the marker
        output_lines = []
        error_lines = []
        
        # Use a thread to read stderr non-blocking
        stderr_queue = queue.Queue()
        def read_stderr():
            try:
                while True:
                    line = self.octave_process.stderr.readline()
                    if line:
                        stderr_queue.put(line.rstrip())
                    else:
                        break
            except:
                pass
        
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stderr_thread.start()
        
        # Read stdout until marker
        while True:
            line = self.octave_process.stdout.readline()
            if not line:
                break
            if marker in line:
                break
            output_lines.append(line.rstrip())
            
            # Safety limit
            if len(output_lines) > 10000:
                break
        
        # Collect any stderr
        while not stderr_queue.empty():
            try:
                error_lines.append(stderr_queue.get_nowait())
            except queue.Empty:
                break
        
        output = "\n".join(output_lines)
        errors = "\n".join(error_lines)
        
        # Check for Octave errors in output
        has_error = bool(errors) or "error:" in output.lower()
        
        return {
            "success": not has_error,
            "output": output,
            "error": errors if errors else None
        }
    
    def execute_code(self, code: str) -> dict:
        """Execute Octave code and return results."""
        self.history.append(code)
        result = self._send_command(code)
        return result
    
    def get_variable(self, name: str) -> dict:
        """Get the value of a variable from the Octave workspace."""
        result = self._send_command(f"disp({name})")
        return result
    
    def set_variable(self, name: str, value: Any) -> dict:
        """Set a variable in the Octave workspace."""
        if isinstance(value, (list, tuple)):
            value_str = "[" + ", ".join(map(str, value)) + "]"
        elif isinstance(value, str):
            value_str = f"'{value}'"
        else:
            value_str = str(value)
        
        result = self._send_command(f"{name} = {value_str};")
        return result
    
    def list_workspace(self) -> dict:
        """List all variables in the current workspace."""
        result = self._send_command("whos")
        return result
    
    def save_figure(self, filename: str = None) -> dict:
        """Save the current figure to a file."""
        if filename is None:
            self.figure_counter += 1
            filename = f"figure_{self.figure_counter}.png"
        
        filepath = os.path.join(self.workspace_dir, filename)
        result = self._send_command(f"print('-dpng', '{filepath}');")
        
        if result["success"] and os.path.exists(filepath):
            result["filepath"] = filepath
            # Optionally encode as base64 for transmission
            with open(filepath, "rb") as f:
                result["base64"] = base64.b64encode(f.read()).decode("utf-8")
        
        return result
    
    def clear_workspace(self) -> dict:
        """Clear all variables from the workspace."""
        result = self._send_command("clear all;")
        return result
    
    def get_help(self, topic: str) -> dict:
        """Get help on an Octave function or topic."""
        result = self._send_command(f"help {topic}")
        return result
    
    def run_script(self, script_path: str) -> dict:
        """Run an Octave .m script file."""
        script_path = os.path.expanduser(script_path)
        
        if not os.path.exists(script_path):
            return {"success": False, "output": "", "error": f"Script not found: {script_path}"}
        
        if not script_path.endswith('.m'):
            return {"success": False, "output": "", "error": "Script must be a .m file"}
        
        result = self._send_command(f"source('{script_path}')")
        return result
    
    def create_script(self, filename: str, code: str) -> dict:
        """Create an Octave script in the workspace directory."""
        if not filename.endswith('.m'):
            filename += '.m'
        
        filepath = os.path.join(self.workspace_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                f.write(code)
            return {"success": True, "output": f"Script saved to {filepath}", "filepath": filepath}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    def list_scripts(self) -> dict:
        """List all .m scripts in the workspace directory."""
        scripts = [f for f in os.listdir(self.workspace_dir) if f.endswith('.m')]
        return {"success": True, "output": "\n".join(scripts) if scripts else "No scripts found", "scripts": scripts}
    
    def shutdown(self):
        """Shutdown the Octave process."""
        if self.octave_process:
            self.octave_process.terminate()
            self.octave_process.wait()
            self.octave_process = None


# MCP Protocol Handler
class MCPProtocolHandler:
    def __init__(self):
        self.server = OctaveMCPServer()
        self.initialized = False
    
    def get_server_info(self) -> dict:
        return {
            "name": "octave-mcp",
            "version": "1.0.0",
            "description": "MCP server for GNU Octave numerical computing"
        }
    
    def get_tools(self) -> list:
        return [
            {
                "name": "octave_execute",
                "description": "Execute Octave/MATLAB code. Returns the output and any errors.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Octave code to execute. Can be multiple lines."
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "octave_get_variable",
                "description": "Get the value of a variable from the Octave workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The variable name to retrieve"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "octave_set_variable",
                "description": "Set a variable in the Octave workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Variable name"},
                        "value": {"description": "Value to set (number, string, or array)"}
                    },
                    "required": ["name", "value"]
                }
            },
            {
                "name": "octave_list_workspace",
                "description": "List all variables currently in the Octave workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "octave_save_figure",
                "description": "Save the current Octave figure to a PNG file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Output filename (optional, auto-generated if not provided)"
                        }
                    }
                }
            },
            {
                "name": "octave_clear",
                "description": "Clear all variables from the Octave workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "octave_help",
                "description": "Get help documentation for an Octave function or topic.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Function or topic name to get help for"
                        }
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "octave_run_script",
                "description": "Run an Octave .m script file from disk.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "script_path": {
                            "type": "string",
                            "description": "Full path to the .m script file"
                        }
                    },
                    "required": ["script_path"]
                }
            },
            {
                "name": "octave_create_script",
                "description": "Create a new Octave .m script file in the workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Name for the script (e.g., 'my_analysis.m')"
                        },
                        "code": {
                            "type": "string",
                            "description": "The Octave code to put in the script"
                        }
                    },
                    "required": ["filename", "code"]
                }
            },
            {
                "name": "octave_list_scripts",
                "description": "List all .m script files in the MCP workspace directory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def handle_tool_call(self, name: str, arguments: dict) -> dict:
        """Handle a tool call from the MCP client."""
        
        # Ensure Octave is running
        if not self.initialized:
            self.server.start_octave()
            self.initialized = True
        
        if name == "octave_execute":
            return self.server.execute_code(arguments["code"])
        elif name == "octave_get_variable":
            return self.server.get_variable(arguments["name"])
        elif name == "octave_set_variable":
            return self.server.set_variable(arguments["name"], arguments["value"])
        elif name == "octave_list_workspace":
            return self.server.list_workspace()
        elif name == "octave_save_figure":
            return self.server.save_figure(arguments.get("filename"))
        elif name == "octave_clear":
            return self.server.clear_workspace()
        elif name == "octave_help":
            return self.server.get_help(arguments["topic"])
        elif name == "octave_run_script":
            return self.server.run_script(arguments["script_path"])
        elif name == "octave_create_script":
            return self.server.create_script(arguments["filename"], arguments["code"])
        elif name == "octave_list_scripts":
            return self.server.list_scripts()
        else:
            return {"success": False, "error": f"Unknown tool: {name}", "output": ""}
    
    def handle_message(self, message: dict) -> dict:
        """Handle an incoming MCP message."""
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": self.get_server_info(),
                    "capabilities": {
                        "tools": {}
                    }
                }
            }
        
        elif method == "initialized":
            # Notification, no response needed
            return None
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": self.get_tools()
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = self.handle_tool_call(tool_name, arguments)
            
            # Format result as MCP content
            content = []
            if result.get("output"):
                content.append({
                    "type": "text",
                    "text": result["output"]
                })
            if result.get("error"):
                content.append({
                    "type": "text",
                    "text": f"Error: {result['error']}"
                })
            if result.get("base64"):
                content.append({
                    "type": "image",
                    "data": result["base64"],
                    "mimeType": "image/png"
                })
            
            if not content:
                content.append({"type": "text", "text": "OK"})
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": content,
                    "isError": not result.get("success", True)
                }
            }
        
        elif method == "shutdown":
            self.server.shutdown()
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": None
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }


def main():
    """Main entry point - runs the MCP server over stdio."""
    handler = MCPProtocolHandler()
    
    # Simple synchronous stdio loop (works on Windows and Unix)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            message = json.loads(line)
            response = handler.handle_message(message)
            
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
