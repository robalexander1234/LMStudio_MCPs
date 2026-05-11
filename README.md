# LMStudio MCPs & Autonomous Email Agent

A collection of Model Context Protocol (MCP) servers for [LM Studio](https://lmstudio.ai/), plus a **fully autonomous email agent** powered by your local LLM.

Коллекция серверов Model Context Protocol (MCP) для [LM Studio](https://lmstudio.ai/) и **полностью автономный email-агент**, работающий на вашей локальной LLM.

🌐 **[English](#-featured-autonomous-email-agent)** | **[Русский](#-автономный-email-агент)**

---

## 🤖 Featured: Autonomous Email Agent

**Email your AI, get intelligent replies.** The email agent runs in the background, monitors your inbox, and uses your local LLM to respond — complete with web search for real-time information.

## 🤖 Автономный email-агент

**Напишите письмо своему ИИ — получите умный ответ.** Email-агент работает в фоновом режиме, отслеживает входящие письма и использует вашу локальную LLM для ответов, включая веб-поиск для получения актуальной информации.

### What It Does / Возможности

| Feature / Функция | Description / Описание |
|---------|-------------|
| 📥 **Auto-Reply / Автоответ** | Monitors inbox every 2 minutes, replies to new emails / Проверяет входящие каждые 2 минуты, отвечает на новые письма |
| 🔍 **Web Search / Веб-поиск** | Automatically searches the web when you ask about news, weather, etc. / Автоматически ищет в интернете новости, погоду и т.д. |
| 🥠 **Fun Outgoing / Исходящие** | Sends fortune cookies, jokes, quotes, and daily digests hourly / Отправляет предсказания, шутки, цитаты и дайджесты каждый час |
| 🧠 **Local LLM / Локальная LLM** | All intelligence runs on YOUR machine via LM Studio / Вся обработка выполняется на ВАШЕЙ машине через LM Studio |
| 🛡️ **New-Only / Только новые** | Only replies to emails received after agent starts (ignores old mail) / Отвечает только на письма, полученные после запуска агента |

### Demo Conversation / Демонстрация

```
You email: "What's the weather in Austin?"
Вы пишете: «Какая погода в Остине?»

Agent / Агент:
  📋 Search decision: SEARCH: weather Austin Texas
  🔍 Searching web for: weather Austin Texas
  ✅ Found 3 search results / Найдено 3 результата
  🤔 Thinking of reply... / Формирую ответ...
  📤 Sending reply... / Отправляю ответ...

You receive / Вы получаете: "Hi! Based on current forecasts, Austin is expecting
highs of 45°F with an Arctic blast moving through the region..."
```

### Quick Start / Быстрый старт

```bash
# 1. Install dependencies / Установите зависимости
pip install ddgs

# 2. Configure your Gmail credentials in the script (see setup below)
#    Настройте учётные данные Gmail в скрипте (см. настройку ниже)

# 3. Start LM Studio with your model loaded (e.g., Llama, Mistral, Qwen, etc.)
#    Запустите LM Studio с загруженной моделью (Llama, Mistral, Qwen и др.)

# 4. Run the agent / Запустите агента
python agent/fun_agent_email.py
```

### Agent Setup / Настройка агента

#### Gmail Configuration / Настройка Gmail

The agent uses Gmail SMTP/IMAP. You need an **App Password** (not your regular password).

Агент использует Gmail SMTP/IMAP. Вам нужен **пароль приложения** (не обычный пароль).

1. Enable 2FA on your Google Account / Включите двухфакторную аутентификацию в аккаунте Google
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords) / Перейдите в [Пароли приложений Google](https://myaccount.google.com/apppasswords)
3. Generate a password for "Mail" / Сгенерируйте пароль для «Почта»
4. Edit the script's `EMAIL_CONFIG` / Отредактируйте `EMAIL_CONFIG` в скрипте:

```python
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "imap_server": "imap.gmail.com",
    "sender_email": "your-bot@gmail.com",        # Bot's email / Email бота
    "sender_password": "xxxx xxxx xxxx xxxx",    # App password / Пароль приложения
    "recipient_email": "your-personal@gmail.com" # Where to send fortunes / Куда отправлять
}
```

#### LM Studio Configuration / Настройка LM Studio

Make sure LM Studio is running with:
- A model loaded (any model works)
- Local server enabled on port 1234 (default)

Убедитесь, что LM Studio запущена с:
- Загруженной моделью (подойдёт любая)
- Включённым локальным сервером на порту 1234 (по умолчанию)

### Agent Commands / Команды агента

```bash
# Run the agent (dual heartbeat loop) / Запуск агента (двойной цикл)
python fun_agent_email.py

# Test commands / Тестовые команды
python fun_agent_email.py test     # Send a test fortune / Отправить тестовое предсказание
python fun_agent_email.py digest   # Send a daily digest / Отправить дайджест
python fun_agent_email.py inbox    # Check inbox and summarize / Проверить входящие
python fun_agent_email.py reply    # Check for emails and reply / Проверить и ответить
python fun_agent_email.py search   # Test web search / Тест веб-поиска
python fun_agent_email.py list     # List recent emails / Список последних писем
```

### Dual Heartbeat System / Система двойного цикла

The agent runs two loops: / Агент работает в двух циклах:

| Loop / Цикл | Interval / Интервал | Action / Действие |
|------|----------|--------|
| **Inbox Check / Проверка входящих** | Every 2 minutes / Каждые 2 минуты | Check for new emails, auto-reply / Проверка новых писем, автоответ |
| **Outgoing Mail / Исходящие** | Every 1 hour / Каждый час | Send fortune/joke/digest / Отправка предсказания/шутки/дайджеста |

Adjust timing in the script: / Настройте интервалы в скрипте:
```python
INBOX_CHECK_INTERVAL = 120    # seconds / секунд
OUTGOING_INTERVAL = 3600      # seconds / секунд
```

### Web Search / Веб-поиск

The agent decides when to search automatically. It will search for:

Агент автоматически решает, когда выполнять поиск. Поиск выполняется для:

- Weather, forecasts / Погода, прогнозы
- News, headlines, current events / Новости, заголовки, текущие события
- Sports scores / Спортивные результаты
- Stock prices / Курсы акций
- Anything "today" / "latest" / "current" / Всё со словами «сегодня» / «последние» / «текущие»

And skip search for: / Поиск пропускается для:

- Greetings ("hi", "how are you") / Приветствия («привет», «как дела»)
- General knowledge it already knows / Общие знания, которые модель уже знает
- Personal questions / Личные вопросы

### Example Emails You Can Send / Примеры писем

| Your Email / Ваше письмо | Agent Response / Ответ агента |
|------------|----------------|
| "What's the weather?" / «Какая погода?» | Searches web, replies with forecast / Ищет в интернете, отвечает прогнозом |
| "Latest AI news?" / «Последние новости ИИ?» | Searches news, summarizes headlines / Ищет новости, подводит итоги |
| "Tell me a joke" / «Расскажи шутку» | Generates a joke (no search needed) / Генерирует шутку (без поиска) |
| "What's 2+2?" / «Сколько будет 2+2?» | Answers directly (no search needed) / Отвечает напрямую (без поиска) |
| "Who won the Super Bowl?" / «Кто выиграл Суперкубок?» | Searches, replies with winner / Ищет, отвечает с результатом |

---

## 📋 MCP Servers / MCP-серверы

In addition to the email agent, this repo includes MCP servers that extend your local LLM's capabilities within LM Studio's chat interface.

Помимо email-агента, репозиторий содержит MCP-серверы, расширяющие возможности вашей локальной LLM в интерфейсе чата LM Studio.

| Server / Сервер | Description / Описание |
|--------|-------------|
| **datetime** | Get current date and time / Текущая дата и время |
| **email** | Send emails via Gmail SMTP / Отправка писем через Gmail SMTP |
| **groq** | Query larger models (Llama 70B) via Groq API / Запросы к большим моделям (Llama 70B) через Groq API |
| **octave** | Execute GNU Octave/MATLAB code / Выполнение кода GNU Octave/MATLAB |
| **python** | Execute Python code with persistent state / Выполнение кода Python с сохранением состояния |
| **websearch** | Search the web via DuckDuckGo / Поиск в интернете через DuckDuckGo |

### Prerequisites / Требования

- **LM Studio** (version with MCP support / версия с поддержкой MCP)
- **Python 3.10+**
- **Windows** (email and octave servers use Windows-specific features / серверы email и octave используют функции Windows)
- For Octave / Для Octave: [GNU Octave](https://octave.org/download) installed / установлен
- For Groq / Для Groq: A [Groq API key](https://console.groq.com/) / Ключ API [Groq](https://console.groq.com/)

### Installation / Установка

```bash
# Clone the repository / Клонируйте репозиторий
git clone https://github.com/yourusername/LMStudio_MCPs.git
cd LMStudio_MCPs

# Install dependencies / Установите зависимости
pip install pytz                                    # datetime
pip install beautifulsoup4 ddgs requests uvicorn    # websearch
pip install mcp groq                                # groq
pip install matplotlib numpy pandas                 # python server
```

---

## MCP Server Details / Подробности о MCP-серверах

### DateTime - Current Date/Time / Текущая дата и время

Returns current date and time in human-readable format.

Возвращает текущую дату и время в удобочитаемом формате.

**Tools / Инструменты:** `get_datetime`

**Configuration / Настройка** (`datetime/server.py`):
```python
tz = pytz.timezone("US/Central")  # Change to your timezone / Измените на ваш часовой пояс
```

---

### Email - Send Emails via Gmail / Отправка писем через Gmail

⚠️ **Requires Gmail App Password setup** (see Agent Setup above)

⚠️ **Требуется настройка пароля приложения Gmail** (см. «Настройка агента» выше)

**Tools / Инструменты:** `send_email`

**Platform / Платформа:** Windows only (uses PowerShell) / Только Windows (использует PowerShell)

---

### Groq - Consult Larger Models / Запрос к большим моделям

"Phone a friend" by querying Llama 3.3 70B via Groq API.

«Звонок другу» — запрос к Llama 3.3 70B через Groq API.

**Tools / Инструменты:** `ask_larger_model`

**Setup / Настройка:**
1. Get API key from [console.groq.com](https://console.groq.com/) / Получите API-ключ на [console.groq.com](https://console.groq.com/)
2. Set in mcp.json (see example below) / Укажите в mcp.json (см. пример ниже)

---

### Octave - Numerical Computing / Численные вычисления

Execute GNU Octave/MATLAB code with persistent workspace.

Выполнение кода GNU Octave/MATLAB с сохранением рабочего пространства.

**Tools / Инструменты:**
- `octave_execute` - Execute code / Выполнить код
- `octave_get_variable` / `octave_set_variable`
- `octave_list_workspace` / `octave_clear`
- `octave_save_figure` - Save plots to PNG / Сохранить графики в PNG
- `octave_help` / `octave_run_script` / `octave_create_script`

**Setup / Настройка:** Update Octave path in `octave/octave_mcp_server.py` / Обновите путь к Octave в `octave/octave_mcp_server.py`

---

### Python - Code Execution / Выполнение кода

Execute Python with persistent namespace between calls.

Выполнение Python с сохранением пространства имён между вызовами.

**Tools / Инструменты:**
- `python_execute` - Execute code / Выполнить код
- `python_get_variable` / `python_set_variable` / `python_list_variables`
- `python_clear` / `python_save_figure`
- `python_create_script` / `python_run_script` / `python_list_scripts`
- `python_pip_install` / `python_help`

---

### Web Search - DuckDuckGo / Веб-поиск — DuckDuckGo

Search the web without API keys.

Поиск в интернете без API-ключей.

**Tools / Инструменты:**
- `web_search` - Search, returns titles/snippets/URLs / Поиск, возвращает заголовки/сниппеты/URL
- `get_page_content` - Fetch and extract page text / Загрузка и извлечение текста страницы

---

## LM Studio Configuration / Настройка LM Studio

### mcp.json Location / Расположение mcp.json

- **Windows:** `%USERPROFILE%\.lmstudio\mcp.json`
- **macOS/Linux:** `~/.lmstudio/mcp.json`

### Complete mcp.json Example / Полный пример mcp.json

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

**Tips / Совет:** Use forward slashes in paths, or escape backslashes (`\\`). / Используйте прямые косые черты в путях или экранируйте обратные (`\\`).

---

## Troubleshooting / Устранение неполадок

### Email Agent Issues / Проблемы email-агента

| Problem / Проблема | Solution / Решение |
|---------|----------|
| Can't connect to LM Studio / Не удаётся подключиться к LM Studio | Ensure LM Studio is running with local server on port 1234 / Убедитесь, что LM Studio запущена с сервером на порту 1234 |
| Search not working / Поиск не работает | Run `pip install ddgs` and test with `python fun_agent_email.py search` / Выполните `pip install ddgs` и проверьте командой `python fun_agent_email.py search` |
| Not replying to emails / Не отвечает на письма | Check Gmail App Password is correct; check IMAP is enabled / Проверьте пароль приложения Gmail и включён ли IMAP |
| Replying to old emails / Отвечает на старые письма | Agent should ignore old mail on startup; check console output / Агент должен игнорировать старые письма; проверьте вывод консоли |

### MCP Server Issues / Проблемы MCP-серверов

| Problem / Проблема | Solution / Решение |
|---------|----------|
| Server not connecting / Сервер не подключается | Check Python path; use full path if needed / Проверьте путь к Python; используйте полный путь |
| Email auth failed / Ошибка авторизации email | Use App Password, not Gmail password / Используйте пароль приложения, а не пароль Gmail |
| Groq API errors / Ошибки Groq API | Check API key; watch for rate limits on free tier / Проверьте API-ключ; следите за лимитами бесплатного тарифа |
| Octave not found / Octave не найден | Update path in `octave_mcp_server.py` / Обновите путь в `octave_mcp_server.py` |

### General Debugging / Общая отладка

Test any server manually: / Тестирование любого сервера вручную:
```bash
python path/to/server.py
```

Then paste: / Затем вставьте:
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

You should see a JSON response. / Вы должны увидеть JSON-ответ.

---

## Project Structure / Структура проекта

```
LMStudio_MCPs/
├── agent/
│   └── fun_agent_email.py    # 🤖 Autonomous email agent / Автономный email-агент
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

## What's Next? / Что дальше?

Ideas for extending the email agent: / Идеи для расширения email-агента:

- **Reminders / Напоминания** - "Remind me in 2 hours" → emails you later / «Напомни через 2 часа» → отправит письмо позже
- **URL Summarizer / Суммаризация URL** - Send a link, get a summary / Отправьте ссылку — получите краткое содержание
- **Daily News Digest / Ежедневный дайджест** - Proactive morning headlines / Утренние заголовки новостей
- **Stock Alerts / Оповещения о акциях** - "Alert me if AAPL drops below $200" / «Уведоми, если AAPL упадёт ниже $200»
- **Todo List / Список задач** - Manage tasks via email / Управление задачами через email
- **Image Generation / Генерация изображений** - Generate images and email them back / Генерация изображений и отправка по email

---

## License / Лицензия

MIT License / Лицензия MIT

## Contributing / Участие в проекте

Contributions welcome! Open an issue or pull request.

Приветствуются любые вклады! Откройте issue или pull request.

---

**Built with local AI in mind.** No cloud dependencies for core functionality — your data stays on your machine.

**Создано для локального ИИ.** Никаких облачных зависимостей для основной функциональности — ваши данные остаются на вашей машине.
