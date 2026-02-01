# LMStudio MCPs & Autonomous Email Agent

A collection of Model Context Protocol (MCP) servers for [LM Studio](https://lmstudio.ai/), plus a **fully autonomous email agent** powered by your local LLM.

---

## 🤖 Featured: Autonomous Email Agent

**Email your AI, get intelligent replies.** The email agent runs in the background, monitors your inbox, and uses your local LLM to respond — complete with web search for real-time information.

### What It Does

| Feature | Description |
|---------|-------------|
| 📥 **Auto-Reply** | Monitors inbox every 2 minutes, replies to new emails |
| 🔍 **Web Search** | Automatically searches the web when you ask about news, weather, etc. |
| 🥠 **Fun Outgoing** | Sends fortune cookies, jokes, quotes, and daily digests hourly |
| 🧠 **Local LLM** | All intelligence runs on YOUR machine via LM Studio |
| 🛡️ **New-Only** | Only replies to emails received after agent starts (ignores old mail) |

### Demo Conversation

```
You email: "What's the weather in Austin?"

Agent:
  📋 Search decision: SEARCH: weather Austin Texas
  🔍 Searching web for: weather Austin Texas
  ✅ Found 3 search results
  🤔 Thinking of reply...
  📤 Sending reply...

You receive: "Hi! Based on current forecasts, Austin is expecting
highs of 45°F with an Arctic blast moving through the region..."
```

### Quick Start

```bash
# 1. Install dependencies
pip install ddgs

# 2. Configure your Gmail credentials in the script (see setup below)

# 3. Start LM Studio with your model loaded (e.g., Llama, Mistral, Qwen, etc.)

# 4. Run the agent
python agent/fun_agent_email.py
```

### Agent Setup

#### Gmail Configuration

The agent uses Gmail SMTP/IMAP. You need an **App Password** (not your regular password).

1. Enable 2FA on your Google Account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a password for "Mail"
4. Edit the script's `EMAIL_CONFIG`:

```python
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "imap_server": "imap.gmail.com",
    "sender_email": "your-bot@gmail.com",        # Bot's email
    "sender_password": "xxxx xxxx xxxx xxxx",    # App password
    "recipient_email": "your-personal@gmail.com" # Where to send fortunes
}
```

#### LM Studio Configuration

Make sure LM Studio is running with:
- A model loaded (any model works)
- Local server enabled on port 1234 (default)

### Agent Commands

```bash
# Run the agent (dual heartbeat loop)
python fun_agent_email.py

# Test commands
python fun_agent_email.py test     # Send a test fortune
python fun_agent_email.py digest   # Send a daily digest
python fun_agent_email.py inbox    # Check inbox and summarize
python fun_agent_email.py reply    # Check for emails and reply
python fun_agent_email.py search   # Test web search
python fun_agent_email.py list     # List recent emails
```

### Dual Heartbeat System

The agent runs two loops:

| Loop | Interval | Action |
|------|----------|--------|
| **Inbox Check** | Every 2 minutes | Check for new emails, auto-reply |
| **Outgoing Mail** | Every 1 hour | Send fortune/joke/digest |

Adjust timing in the script:
```python
INBOX_CHECK_INTERVAL = 120    # seconds
OUTGOING_INTERVAL = 3600      # seconds
```

### Web Search

The agent decides when to search automatically. It will search for:
- Weather, forecasts
- News, headlines, current events
- Sports scores
- Stock prices
- Anything "today" / "latest" / "current"

And skip search for:
- Greetings ("hi", "how are you")
- General knowledge it already knows
- Personal questions

### Example Emails You Can Send

| Your Email | Agent Response |
|------------|----------------|
| "What's the weather?" | Searches web, replies with forecast |
| "Latest AI news?" | Searches news, summarizes headlines |
| "Tell me a joke" | Generates a joke (no search needed) |
| "What's 2+2?" | Answers directly (no search needed) |
| "Who won the Super Bowl?" | Searches, replies with winner |

---

## 📋 MCP Servers

In addition to the email agent, this repo includes MCP servers that extend your local LLM's capabilities within LM Studio's chat interface.

| Server | Description |
|--------|-------------|
| **datetime** | Get current date and time |
| **email** | Send emails via Gmail SMTP |
| **groq** | Query larger models (Llama 70B) via Groq API |
| **octave** | Execute GNU Octave/MATLAB code |
| **python** | Execute Python code with persistent state |
| **websearch** | Search the web via DuckDuckGo |

### Prerequisites

- **LM Studio** (version with MCP support)
- **Python 3.10+**
- **Windows** (email and octave servers use Windows-specific features)
- For Octave: [GNU Octave](https://octave.org/download) installed
- For Groq: A [Groq API key](https://console.groq.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/LMStudio_MCPs.git
cd LMStudio_MCPs

# Install dependencies
pip install pytz                                    # datetime
pip install beautifulsoup4 ddgs requests uvicorn    # websearch
pip install mcp groq                                # groq
pip install matplotlib numpy pandas                 # python server
```

---

## MCP Server Details

### DateTime - Current Date/Time

Returns current date and time in human-readable format.

**Tools:** `get_datetime`

**Configuration** (`datetime/server.py`):
```python
tz = pytz.timezone("US/Central")  # Change to your timezone
```

---

### Email - Send Emails via Gmail

⚠️ **Requires Gmail App Password setup** (see Agent Setup above)

**Tools:** `send_email`

**Platform:** Windows only (uses PowerShell)

---

### Groq - Consult Larger Models

"Phone a friend" by querying Llama 3.3 70B via Groq API.

**Tools:** `ask_larger_model`

**Setup:**
1. Get API key from [console.groq.com](https://console.groq.com/)
2. Set in mcp.json (see example below)

---

### Octave - Numerical Computing

Execute GNU Octave/MATLAB code with persistent workspace.

**Tools:**
- `octave_execute` - Execute code
- `octave_get_variable` / `octave_set_variable`
- `octave_list_workspace` / `octave_clear`
- `octave_save_figure` - Save plots to PNG
- `octave_help` / `octave_run_script` / `octave_create_script`

**Setup:** Update Octave path in `octave/octave_mcp_server.py`

---

### Python - Code Execution

Execute Python with persistent namespace between calls.

**Tools:**
- `python_execute` - Execute code
- `python_get_variable` / `python_set_variable` / `python_list_variables`
- `python_clear` / `python_save_figure`
- `python_create_script` / `python_run_script` / `python_list_scripts`
- `python_pip_install` / `python_help`

---

### Web Search - DuckDuckGo

Search the web without API keys.

**Tools:**
- `web_search` - Search, returns titles/snippets/URLs
- `get_page_content` - Fetch and extract page text

---

## LM Studio Configuration

### mcp.json Location

- **Windows:** `%USERPROFILE%\.lmstudio\mcp.json`
- **macOS/Linux:** `~/.lmstudio/mcp.json`

### Complete mcp.json Example

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
      "args": ["C:/Users/YourName/LMStudio_MCPs/groq/server.py"],
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

**Tip:** Use forward slashes in paths, or escape backslashes (`\\`).

---

## Troubleshooting

### Email Agent Issues

| Problem | Solution |
|---------|----------|
| Can't connect to LM Studio | Ensure LM Studio is running with local server on port 1234 |
| Search not working | Run `pip install ddgs` and test with `python fun_agent_email.py search` |
| Not replying to emails | Check Gmail App Password is correct; check IMAP is enabled in Gmail settings |
| Replying to old emails | Agent should ignore old mail on startup; check console output |

### MCP Server Issues

| Problem | Solution |
|---------|----------|
| Server not connecting | Check Python path; use full path if needed |
| Email auth failed | Use App Password, not Gmail password |
| Groq API errors | Check API key; watch for rate limits on free tier |
| Octave not found | Update path in `octave_mcp_server.py` |

### General Debugging

Test any server manually:
```bash
python path/to/server.py
```

Then paste:
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

You should see a JSON response.

---

## Project Structure

```
LMStudio_MCPs/
├── agent/
│   └── fun_agent_email.py    # 🤖 Autonomous email agent
├── datetime/
│   └── server.py
├── email/
│   └── server.py
├── groq/
│   └── server.py
├── octave/
│   └── octave_mcp_server.py
├── python/
│   └── python_mcp_server.py
├── websearch/
│   └── main.py
└── README.md
```

---

## What's Next?

Ideas for extending the email agent:

- **Reminders** - "Remind me in 2 hours" → emails you later
- **URL Summarizer** - Send a link, get a summary
- **Daily News Digest** - Proactive morning headlines
- **Stock Alerts** - "Alert me if AAPL drops below $200"
- **Todo List** - Manage tasks via email
- **Image Generation** - Generate images and email them back

---

## License

MIT License

## Contributing

Contributions welcome! Open an issue or pull request.

---

**Built with local AI in mind.** No cloud dependencies for core functionality — your data stays on your machine.
