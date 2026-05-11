# LMStudio MCPs & Autonomous Email Agent

A collection of Model Context Protocol (MCP) servers for [LM Studio](https://lmstudio.ai/), plus a **fully autonomous email agent** powered by your local LLM.

---

## 🇷🇺 MCP серверы и Автономный Email-Агент для LM Studio

**Коллекция Model Context Protocol серверов + полностью автономный email-агент на локальной LLM для [LM Studio](https://lmstudio.ai/)**

### Что умеет

| Компонент | Описание |
|---------|-------------|
| 📧 **Email-Агент** | Читает почту каждые 2 мин, отвечает сам с веб-поиском |
| 🥠 **Авторассылка** | Шлет fortune cookie, шутки, дайджесты каждый час |
| 🧠 **Локальный LLM** | Весь интеллект работает на ТВОЕЙ машине через LM Studio |
| 🔧 **MCP Серверы** | Python, Octave, веб-поиск, время, Groq, отправка email |
| 🔌 **JAN AI Shim** | Подключение моделей JAN к LM Studio через MCP |

### Быстрый старт за 2 минуты

```bash
# 1. Установи зависимости
pip install ddgs

# 2. Настрой Gmail App Password в agent/fun_agent_email.py

# 3. Запусти LM Studio с моделью на порту 1234

# 4. Запуск агента
python agent/fun_agent_email.py