# Python MCP Server for LMStudio

Execute Python code directly from your LLM conversations in LMStudio.

## Features

- **python_execute** - Run arbitrary Python code with persistent variables
- **python_get_variable** - Retrieve variable values
- **python_set_variable** - Set variables from the LLM
- **python_list_variables** - List all user-defined variables
- **python_clear** - Clear the session
- **python_save_figure** - Save matplotlib plots and return as base64
- **python_create_script** - Create .py files in the workspace
- **python_run_script** - Run saved scripts
- **python_list_scripts** - List available scripts
- **python_pip_install** - Install packages on the fly
- **python_help** - Get Python help documentation

## Installation

1. Copy `python_mcp_server.py` to a folder (e.g., `C:\Users\alexa\python-mcp\`)

2. Test the server:
   ```
   python test_server.py
   ```

3. Add to your LMStudio `mcp.json`:

```json
{
  "mcpServers": {
    "python": {
      "command": "C:\\Users\\alexa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\alexa\\python-mcp\\python_mcp_server.py"]
    }
  }
}
```

4. Restart LMStudio

## Example mcp.json with Multiple Servers

```json
{
  "mcpServers": {
    "python": {
      "command": "C:\\Users\\alexa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\alexa\\python-mcp\\python_mcp_server.py"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\alexa\\Desktop", "C:\\Users\\alexa\\Documents"]
    },
    "web-search": {
      "command": "C:\\Users\\alexa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\alexa\\web-search-mcp-lmstudio\\main.py"]
    },
    "email": {
      "command": "C:\\Users\\alexa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\alexa\\email-mcp\\server.py"]
    },
    "datetime": {
      "command": "C:\\Users\\alexa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\alexa\\datetime-mcp\\server.py"]
    },
    "groq": {
      "command": "C:\\Users\\alexa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\alexa\\groq-mcp\\server.py"]
    }
  }
}
```

## Usage Examples

Once configured, you can ask your LLM things like:

- "Calculate the factorial of 20"
- "Create a numpy array and find its eigenvalues"
- "Plot a sine wave and save it"
- "Install pandas and load a CSV file"
- "Create a script that processes text files"

## Workspace

Scripts and figures are saved to a `workspace` folder next to the server script.

## Troubleshooting

### Server doesn't load
- Check the Python path in mcp.json matches your installation
- Run `python python_mcp_server.py` manually to see errors
- Run `python test_server.py` to verify it works

### Import errors
- Use `python_pip_install` to install missing packages
- Make sure you're using the same Python installation in mcp.json

### Plots not working
- Install matplotlib: `pip install matplotlib`
- The server saves plots to the workspace folder
