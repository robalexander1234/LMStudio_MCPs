# LMStudio MCPs

A collection of Model Context Protocol (MCP) servers designed for use with [LM Studio](https://lmstudio.ai/). These servers extend your local LLM's capabilities with tools for executing code, sending emails, searching the web, and consulting larger cloud models.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [MCP Servers](#mcp-servers)
  - [DateTime](#datetime---current-datetime)
  - [Email](#email---send-emails-via-gmail)
  - [Groq](#groq---consult-larger-models)
  - [Octave](#octave---numerical-computing)
  - [Python](#python---python-code-execution)
  - [Web Search](#web-search---duckduckgo-search)
- [LM Studio Configuration](#lm-studio-configuration)
- [Complete mcp.json Example](#complete-mcpjson-example)
- [Troubleshooting](#troubleshooting)

## Overview

MCP (Model Context Protocol) allows LLMs to use external tools. When running a local model in LM Studio, these MCP servers give your model superpowers:

| Server | Description |
|--------|-------------|
| **datetime** | Get current date and time |
| **email** | Send emails via Gmail SMTP |
| **groq** | Query larger models (Llama 70B) via Groq API |
| **octave** | Execute GNU Octave/MATLAB code |
| **python** | Execute Python code with persistent state |
| **websearch** | Search the web via DuckDuckGo |

## Prerequisites

- **LM Studio** (version with MCP support)
- **Python 3.10+** installed and accessible from command line
- **Windows** (the email and octave servers use Windows-specific features)
- For Octave server: [GNU Octave](https://octave.org/download) installed
- For Groq server: A [Groq API key](https://console.groq.com/)

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/yourusername/LMStudio_MCPs.git
   cd LMStudio_MCPs
   ```

2. **Install Python dependencies for each server you want to use:**

   ```bash
   # For datetime (minimal dependencies)
   pip install pytz

   # For websearch
   pip install beautifulsoup4 duckduckgo-search fastmcp requests uvicorn

   # For groq
   pip install mcp groq

   # For python server (matplotlib optional but recommended)
   pip install matplotlib numpy pandas
   ```

3. **Configure LM Studio** (see [LM Studio Configuration](#lm-studio-configuration))

---

## MCP Servers

### DateTime - Current Date/Time

A simple server that returns the current date and time in a human-readable format.

**Tools provided:**
- `get_datetime` - Returns current date/time (e.g., "Monday, January 27, 2025 at 02:30:45 PM CST")

**Configuration:**
Edit `datetime/server.py` to change your timezone:
```python
tz = pytz.timezone("US/Central")  # Change to your timezone
```

Common timezone values: `US/Eastern`, `US/Pacific`, `Europe/London`, `Asia/Tokyo`

**mcp.json entry:**
```json
{
  "datetime": {
    "command": "python",
    "args": ["C:/path/to/LMStudio_MCPs/datetime/server.py"]
  }
}
```

---

### Email - Send Emails via Gmail

⚠️ **Requires Setup** - This server allows your LLM to send emails through Gmail.

**Tools provided:**
- `send_email` - Send an email with recipient, subject, and body

#### Gmail Setup Instructions

This server uses Gmail's SMTP with an **App Password** (not your regular Gmail password).

**Step 1: Enable 2-Factor Authentication**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google," enable **2-Step Verification**

**Step 2: Generate an App Password**
1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select app: **Mail**
3. Select device: **Windows Computer** (or other)
4. Click **Generate**
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

**Step 3: Configure the Server**

Edit `email/server.py` and replace the placeholder credentials:

```python
$smtp.Credentials = New-Object System.Net.NetworkCredential('your-email@gmail.com', 'your-app-password')
$smtp.Send('your-email@gmail.com', '{to}', '{subject}', '{body}')
```

Replace:
- `your-email@gmail.com` with your Gmail address (appears twice)
- `your-app-password` with the 16-character app password from Step 2

**Example:**
```python
$smtp.Credentials = New-Object System.Net.NetworkCredential('john.doe@gmail.com', 'abcd efgh ijkl mnop')
$smtp.Send('john.doe@gmail.com', '{to}', '{subject}', '{body}')
```

**Security Notes:**
- ⚠️ Never commit your real credentials to version control
- The app password only works for SMTP, not for logging into Gmail
- You can revoke app passwords anytime from your Google Account

**mcp.json entry:**
```json
{
  "email": {
    "command": "python",
    "args": ["C:/path/to/LMStudio_MCPs/email/server.py"]
  }
}
```

**Platform Note:** This server uses PowerShell and only works on Windows.

---

### Groq - Consult Larger Models

This server allows your local LLM to "phone a friend" by querying Llama 3.3 70B via the Groq API. Useful when your local model needs help with complex questions.

**Tools provided:**
- `ask_larger_model` - Send a question to Llama 70B and get a response

#### Groq Setup Instructions

**Step 1: Get a Groq API Key**
1. Sign up at [console.groq.com](https://console.groq.com/)
2. Navigate to API Keys
3. Create a new API key

**Step 2: Set Environment Variable**

**Windows (Command Prompt):**
```cmd
setx GROQ_API_KEY "gsk_your_api_key_here"
```

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("GROQ_API_KEY", "gsk_your_api_key_here", "User")
```

**Linux/macOS:**
```bash
export GROQ_API_KEY="gsk_your_api_key_here"
# Add to ~/.bashrc or ~/.zshrc to persist
```

**Step 3: Restart LM Studio** after setting the environment variable.

**mcp.json entry:**
```json
{
  "groq": {
    "command": "python",
    "args": ["C:/path/to/LMStudio_MCPs/grok/server.py"]
  }
}
```

---

### Octave - Numerical Computing

Execute GNU Octave/MATLAB code directly from your LLM. Maintains a persistent Octave session with workspace variables.

**Tools provided:**
- `octave_execute` - Execute Octave/MATLAB code
- `octave_get_variable` - Get a variable's value
- `octave_set_variable` - Set a variable
- `octave_list_workspace` - List all workspace variables
- `octave_save_figure` - Save current plot to PNG
- `octave_clear` - Clear workspace
- `octave_help` - Get help on functions
- `octave_run_script` - Run a .m script file
- `octave_create_script` - Create a new .m script
- `octave_list_scripts` - List scripts in workspace

#### Octave Setup Instructions

**Step 1: Install GNU Octave**
1. Download from [octave.org/download](https://octave.org/download)
2. Install to the default location

**Step 2: Update the Server Path**

Edit `octave/octave_mcp_server.py` and update the Octave path if different:

```python
self.octave_process = subprocess.Popen(
    [r"C:\Program Files\GNU Octave\Octave-10.1.0\octave-launch.exe", 
     "--no-gui", "--interactive", "--quiet"],
    ...
)
```

**mcp.json entry:**
```json
{
  "octave": {
    "command": "python",
    "args": ["C:/path/to/LMStudio_MCPs/octave/octave_mcp_server.py"]
  }
}
```

**Platform Note:** The default configuration is for Windows. For Linux/macOS, change the Octave path to just `"octave"` (assuming it's in your PATH).

---

### Python - Python Code Execution

Execute Python code with a persistent namespace. Variables, imports, and state persist between calls.

**Tools provided:**
- `python_execute` - Execute Python code
- `python_get_variable` - Get a variable's value
- `python_set_variable` - Set a variable
- `python_list_variables` - List all user-defined variables
- `python_clear` - Clear all variables
- `python_save_figure` - Save matplotlib figure
- `python_create_script` - Create a .py script
- `python_run_script` - Run a script from workspace
- `python_list_scripts` - List scripts in workspace
- `python_pip_install` - Install packages via pip
- `python_help` - Get help on Python topics

**mcp.json entry:**
```json
{
  "python": {
    "command": "python",
    "args": ["C:/path/to/LMStudio_MCPs/python/python_mcp_server.py"]
  }
}
```

Scripts and figures are saved to the `python/workspace/` directory.

---

### Web Search - DuckDuckGo Search

Search the web and fetch page content using DuckDuckGo (no API key required).

**Tools provided:**
- `web_search` - Search the web, returns titles, snippets, and URLs
- `get_page_content` - Fetch and extract text from a webpage

**Dependencies:**
```bash
pip install beautifulsoup4 duckduckgo-search fastmcp requests uvicorn
```

**mcp.json entry:**
```json
{
  "websearch": {
    "command": "python",
    "args": ["C:/path/to/LMStudio_MCPs/websearch/main.py"]
  }
}
```

---

## LM Studio Configuration

MCP servers are configured in LM Studio's `mcp.json` file.

### Locating mcp.json

The file is typically located at:
- **Windows:** `%USERPROFILE%\.lmstudio\mcp.json`
- **macOS:** `~/.lmstudio/mcp.json`
- **Linux:** `~/.lmstudio/mcp.json`

If the file doesn't exist, create it.

### Configuration Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["path/to/server.py"]
    }
  }
}
```

**Important:** Use forward slashes (`/`) in paths, even on Windows, or escape backslashes (`\\`).

---

## Complete mcp.json Example

Here's a complete configuration with all servers (adjust paths to match your setup):

```json
{
  "mcpServers": {
    "datetime": {
      "command": "python",
      "args": ["C:/Users/YourName/LMStudio_MCPs/datetime/server.py"]
    },
    "email": {
      "command": "python",
      "args": ["C:/Users/YourName/LMStudio_MCPs/email/server.py"]
    },
    "groq": {
      "command": "python",
      "args": ["C:/Users/YourName/LMStudio_MCPs/grok/server.py"],
      "env": {
        "GROQ_API_KEY": "gsk_your_api_key_here"
      }
    },
    "octave": {
      "command": "python",
      "args": ["C:/Users/YourName/LMStudio_MCPs/octave/octave_mcp_server.py"]
    },
    "python": {
      "command": "python",
      "args": ["C:/Users/YourName/LMStudio_MCPs/python/python_mcp_server.py"]
    },
    "websearch": {
      "command": "python",
      "args": ["C:/Users/YourName/LMStudio_MCPs/websearch/main.py"]
    }
  }
}
```

**Alternative: Specify full Python path** if `python` isn't in your PATH:
```json
{
  "command": "C:/Users/YourName/AppData/Local/Programs/Python/Python312/python.exe",
  "args": ["C:/Users/YourName/LMStudio_MCPs/datetime/server.py"]
}
```

---

## Troubleshooting

### Server Not Connecting

1. **Check Python path:** Run `python --version` in terminal. If not found, use the full path to python.exe.
2. **Check file paths:** Ensure paths in mcp.json are correct and use forward slashes.
3. **Restart LM Studio:** After changing mcp.json, restart LM Studio completely.

### Email Server Issues

- **Authentication failed:** Ensure you're using an App Password, not your Gmail password.
- **Connection refused:** Check your firewall isn't blocking outbound SMTP (port 587).
- **"Less secure apps" error:** You need 2FA enabled and an App Password.

### Groq Server Issues

- **API key not found:** Ensure `GROQ_API_KEY` environment variable is set and LM Studio was restarted.
- **Rate limits:** Groq has rate limits on the free tier; wait and retry.

### Octave Server Issues

- **Octave not found:** Update the path in `octave_mcp_server.py` to match your installation.
- **Graphics issues:** The server uses gnuplot; ensure it's installed with Octave.

### General Debugging

Test a server manually to see error messages:
```bash
python path/to/server.py
```

Then paste this JSON and press Enter:
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

You should see a JSON response. Press Ctrl+C to exit.

---

## License

MIT License - See individual server directories for any additional licenses.

## Contributing

Contributions welcome! Please open an issue or pull request.
