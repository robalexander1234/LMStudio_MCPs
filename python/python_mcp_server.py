#!/usr/bin/env python3
"""
Python MCP Server for LMStudio
Enables LLMs to execute Python code, manage variables, create plots, and run scripts.

Usage:
    python python_mcp_server.py

Add to LMStudio mcp.json:
{
  "mcpServers": {
    "python": {
      "command": "C:\\Users\\alexa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\alexa\\python-mcp\\python_mcp_server.py"]
    }
  }
}
"""

import sys
import json
import io
import os
import traceback
import base64
import subprocess
from contextlib import redirect_stdout, redirect_stderr

# Persistent namespace for variable storage between calls
PYTHON_NAMESPACE = {
    '__builtins__': __builtins__,
    '__name__': '__main__',
}

# Directory for scripts and figures
WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# Tool definitions
TOOLS = [
    {
        "name": "python_execute",
        "description": "Execute Python code. Variables persist between calls. Returns stdout, stderr, and the result of the last expression.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "python_get_variable",
        "description": "Get the value of a variable from the Python session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Variable name to retrieve"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "python_set_variable",
        "description": "Set a variable in the Python session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Variable name"
                },
                "value": {
                    "type": "string",
                    "description": "Value as a Python literal (e.g., '42', '[1,2,3]', '\"hello\"')"
                }
            },
            "required": ["name", "value"]
        }
    },
    {
        "name": "python_list_variables",
        "description": "List all user-defined variables in the Python session",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "python_clear",
        "description": "Clear all user-defined variables from the session",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "python_save_figure",
        "description": "Save the current matplotlib figure to a file and return it as base64",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename for the figure (e.g., 'plot.png')"
                }
            },
            "required": ["filename"]
        }
    },
    {
        "name": "python_create_script",
        "description": "Create a Python script file in the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Script filename (e.g., 'analysis.py')"
                },
                "code": {
                    "type": "string",
                    "description": "Python code for the script"
                }
            },
            "required": ["filename", "code"]
        }
    },
    {
        "name": "python_run_script",
        "description": "Run a Python script from the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Script filename to run"
                }
            },
            "required": ["filename"]
        }
    },
    {
        "name": "python_list_scripts",
        "description": "List all Python scripts in the workspace",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "python_pip_install",
        "description": "Install a Python package using pip",
        "inputSchema": {
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Package name to install (e.g., 'numpy', 'pandas==2.0.0')"
                }
            },
            "required": ["package"]
        }
    },
    {
        "name": "python_help",
        "description": "Get help on a Python object, module, or function",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to get help on (e.g., 'list', 'numpy.array', 'print')"
                }
            },
            "required": ["topic"]
        }
    }
]


def execute_python(code):
    """Execute Python code and return results."""
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    result = None
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Try to eval first (for expressions)
            try:
                result = eval(code, PYTHON_NAMESPACE)
            except SyntaxError:
                # If eval fails, use exec (for statements)
                exec(code, PYTHON_NAMESPACE)
                result = None
    except Exception as e:
        stderr_capture.write(f"\n{type(e).__name__}: {e}\n")
        stderr_capture.write(traceback.format_exc())
    
    return {
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "result": repr(result) if result is not None else None
    }


def get_variable(name):
    """Get a variable from the namespace."""
    if name in PYTHON_NAMESPACE:
        value = PYTHON_NAMESPACE[name]
        return {
            "name": name,
            "value": repr(value),
            "type": type(value).__name__
        }
    else:
        return {"error": f"Variable '{name}' not found"}


def set_variable(name, value_str):
    """Set a variable in the namespace."""
    try:
        value = eval(value_str, PYTHON_NAMESPACE)
        PYTHON_NAMESPACE[name] = value
        return {"success": True, "name": name, "value": repr(value)}
    except Exception as e:
        return {"error": str(e)}


def list_variables():
    """List user-defined variables."""
    skip = {'__builtins__', '__name__', '__doc__', '__package__', '__loader__', '__spec__'}
    variables = []
    for name, value in PYTHON_NAMESPACE.items():
        if name not in skip and not name.startswith('_'):
            variables.append({
                "name": name,
                "type": type(value).__name__,
                "value": repr(value)[:100]  # Truncate long values
            })
    return variables


def clear_variables():
    """Clear user-defined variables."""
    global PYTHON_NAMESPACE
    skip = {'__builtins__', '__name__', '__doc__', '__package__', '__loader__', '__spec__'}
    keys_to_remove = [k for k in PYTHON_NAMESPACE.keys() if k not in skip]
    for key in keys_to_remove:
        del PYTHON_NAMESPACE[key]
    return {"cleared": len(keys_to_remove)}


def save_figure(filename):
    """Save matplotlib figure to file and return base64."""
    try:
        import matplotlib.pyplot as plt
        filepath = os.path.join(WORKSPACE_DIR, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        with open(filepath, 'rb') as f:
            b64_data = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            "success": True,
            "filepath": filepath,
            "base64": b64_data
        }
    except Exception as e:
        return {"error": str(e)}


def create_script(filename, code):
    """Create a Python script in the workspace."""
    if not filename.endswith('.py'):
        filename += '.py'
    filepath = os.path.join(WORKSPACE_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        return {"success": True, "filepath": filepath}
    except Exception as e:
        return {"error": str(e)}


def run_script(filename):
    """Run a Python script from the workspace."""
    if not filename.endswith('.py'):
        filename += '.py'
    filepath = os.path.join(WORKSPACE_DIR, filename)
    
    if not os.path.exists(filepath):
        return {"error": f"Script not found: {filename}"}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        return execute_python(code)
    except Exception as e:
        return {"error": str(e)}


def list_scripts():
    """List Python scripts in the workspace."""
    scripts = []
    for f in os.listdir(WORKSPACE_DIR):
        if f.endswith('.py'):
            filepath = os.path.join(WORKSPACE_DIR, f)
            size = os.path.getsize(filepath)
            scripts.append({"filename": f, "size": size})
    return scripts


def pip_install(package):
    """Install a package using pip."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package],
            capture_output=True,
            text=True,
            timeout=120
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"error": "Installation timed out after 120 seconds"}
    except Exception as e:
        return {"error": str(e)}


def get_help(topic):
    """Get help on a Python topic."""
    stdout_capture = io.StringIO()
    try:
        with redirect_stdout(stdout_capture):
            # Try to evaluate the topic first
            try:
                obj = eval(topic, PYTHON_NAMESPACE)
                help(obj)
            except:
                # If that fails, try importing it
                try:
                    exec(f"import {topic.split('.')[0]}", PYTHON_NAMESPACE)
                    obj = eval(topic, PYTHON_NAMESPACE)
                    help(obj)
                except:
                    return {"error": f"Could not find help for '{topic}'"}
        return {"help": stdout_capture.getvalue()}
    except Exception as e:
        return {"error": str(e)}


def handle_tool_call(name, arguments):
    """Handle a tool call and return results."""
    if name == "python_execute":
        return execute_python(arguments["code"])
    elif name == "python_get_variable":
        return get_variable(arguments["name"])
    elif name == "python_set_variable":
        return set_variable(arguments["name"], arguments["value"])
    elif name == "python_list_variables":
        return list_variables()
    elif name == "python_clear":
        return clear_variables()
    elif name == "python_save_figure":
        return save_figure(arguments["filename"])
    elif name == "python_create_script":
        return create_script(arguments["filename"], arguments["code"])
    elif name == "python_run_script":
        return run_script(arguments["filename"])
    elif name == "python_list_scripts":
        return list_scripts()
    elif name == "python_pip_install":
        return pip_install(arguments["package"])
    elif name == "python_help":
        return get_help(arguments["topic"])
    else:
        return {"error": f"Unknown tool: {name}"}


def send_response(response):
    """Send a JSON-RPC response."""
    response_str = json.dumps(response)
    sys.stdout.write(response_str + "\n")
    sys.stdout.flush()


def main():
    """Main server loop using JSON-RPC over stdio."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            method = request.get("method", "")
            req_id = request.get("id")
            params = request.get("params", {})
            
            if method == "initialize":
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "python-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                })
            
            elif method == "notifications/initialized":
                pass  # No response needed for notifications
            
            elif method == "tools/list":
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS
                    }
                })
            
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = handle_tool_call(tool_name, arguments)
                
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                })
            
            else:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                })
        
        except json.JSONDecodeError as e:
            send_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                }
            })
        except Exception as e:
            send_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}"
                }
            })


if __name__ == "__main__":
    main()
