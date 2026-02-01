"""
Fun Proactive Agent for LM Studio - WITH EMAIL
Sends fortunes, jokes, and fun stuff to your inbox
"""

import time
import json
import random
import requests
import smtplib
import imaplib
import email
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime
from pathlib import Path

# Try to import search library
try:
    from ddgs import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    try:
        # Fallback to old package name
        from duckduckgo_search import DDGS
        SEARCH_AVAILABLE = True
    except ImportError:
        SEARCH_AVAILABLE = False
        print("⚠️  Web search disabled. Install with: pip install ddgs")

# === CONFIGURATION ===
LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"

# Dual heartbeat system
INBOX_CHECK_INTERVAL = 120    # 2 minutes - check for emails to reply to
OUTGOING_INTERVAL = 3600      # 1 hour - send fortunes, digests, etc.

MEMORY_FILE = Path("agent_memory.json")
FORTUNE_LOG = Path("fortunes.txt")

# Track when agent started (only reply to emails after this)
AGENT_START_TIME = None

# === EMAIL CONFIG ===
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "imap_server": "imap.gmail.com",
    "sender_email": "sender@gmail.com",
    "sender_password": "gmail api key",         # Your app password
    "recipient_email": "recipient@gmail.com"
}

# === READ EMAIL FUNCTIONS ===
def read_recent_emails(count=5, unread_only=True):
    """Read recent emails from inbox."""
    try:
        mail = imaplib.IMAP4_SSL(EMAIL_CONFIG["imap_server"])
        mail.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        mail.select("inbox")
        
        # Search for emails
        if unread_only:
            status, messages = mail.search(None, "UNSEEN")
        else:
            status, messages = mail.search(None, "ALL")
        
        email_ids = messages[0].split()
        
        # Get the most recent ones
        recent_ids = email_ids[-count:] if len(email_ids) >= count else email_ids
        
        emails = []
        for email_id in reversed(recent_ids):  # Most recent first
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")
                    
                    # Get sender
                    from_addr = msg.get("From", "Unknown")
                    
                    # Get date
                    date = msg.get("Date", "Unknown")
                    
                    # Get body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")
                    
                    emails.append({
                        "id": email_id.decode(),
                        "from": from_addr,
                        "subject": subject,
                        "date": date,
                        "body": body[:1000]  # Truncate long emails
                    })
        
        mail.logout()
        return emails
        
    except Exception as e:
        print(f"❌ Error reading email: {e}")
        return []

def summarize_emails_with_llm(emails):
    """Use LM Studio to summarize emails."""
    if not emails:
        return "No new emails to summarize."
    
    email_text = ""
    for i, e in enumerate(emails, 1):
        email_text += f"\n--- Email {i} ---\n"
        email_text += f"From: {e['from']}\n"
        email_text += f"Subject: {e['subject']}\n"
        email_text += f"Body: {e['body'][:500]}...\n"
    
    prompt = f"""Summarize these emails briefly. For each one, give:
- Who it's from
- What it's about (1 sentence)
- If any action is needed

{email_text}"""
    
    response = call_llm([{"role": "user", "content": prompt}], max_tokens=800)
    return response or "Could not summarize emails."

def check_and_report_emails(memory):
    """Check for new emails and send a summary."""
    print("📬 Checking for new emails...")
    emails = read_recent_emails(count=5, unread_only=True)
    
    if not emails:
        print("   No unread emails.")
        return None
    
    print(f"   Found {len(emails)} unread email(s)")
    summary = summarize_emails_with_llm(emails)
    
    subject = f"📬 Email Summary: {len(emails)} new message(s)"
    body = f"""<h3>Your AI checked your inbox!</h3>
    <p>Found {len(emails)} unread email(s). Here's the summary:</p>
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
        {summary.replace(chr(10), '<br>')}
    </div>
    <hr>
    <p style="color: #888; font-size: 12px;">
        Checked: {EMAIL_CONFIG['sender_email']}
    </p>"""
    
    return send_email(subject, body)

# === AUTO-REPLY SYSTEM ===
def get_sender_email(from_header):
    """Extract just the email address from a From header."""
    import re
    match = re.search(r'[\w\.-]+@[\w\.-]+', from_header)
    return match.group(0) if match else from_header

def generate_reply_with_context(original_email, search_results=None):
    """Use Mistral to generate a reply to an email, with optional search results."""
    
    # Build the prompt
    context = ""
    if search_results:
        context = f"""
I searched the web and found this information:
{search_results}

Use this information to answer their question accurately.
"""
    
    prompt = f"""You are a helpful AI assistant responding to an email.
You are powered by Mistral, running locally via LM Studio.

{context}
The email you received:
From: {original_email['from']}
Subject: {original_email['subject']}
Message: {original_email['body'][:1500]}

Write a helpful, friendly reply. Be concise but warm.
If you used search results, cite the information naturally.
If they ask something you don't know and no search results are provided, say so honestly.

Sign off as "Your AI Assistant 🤖"

Just write the reply, no subject line needed."""

    response = call_llm([{"role": "user", "content": prompt}], max_tokens=800)
    return response

def check_and_search(original_email):
    """Check if the email needs a web search, and perform it if so."""
    
    today = datetime.now().strftime("%B %d, %Y")
    
    # Ask Mistral if search is needed
    check_prompt = f"""Does this email need a web search? Today is {today}.

Email subject: {original_email['subject']}
Email body: {original_email['body'][:500]}

ALWAYS search for:
- Weather, forecasts
- News, headlines, current events
- Sports scores, game results
- Stock prices, market info
- Recent events, "what happened"
- Anything asking about "today" or "latest" or "current"

NO search needed for:
- Greetings ("hi", "hello", "how are you")
- General knowledge you already know (capitals, math, definitions)
- Personal questions ("what's your name")
- Opinions or advice

If search needed, respond: SEARCH: <short query 3-6 words>
If no search needed, respond: NO_SEARCH

Your response:"""

    response = call_llm([{"role": "user", "content": check_prompt}], max_tokens=50)
    
    if not response:
        return None
    
    response = response.strip()
    print(f"   📋 Search decision: {response}")
    
    if response.upper().startswith("SEARCH:"):
        query = response.split(":", 1)[1].strip()
        # Remove any remaining braces or placeholders
        query = query.replace("{", "").replace("}", "").replace("[", "").replace("]", "")
        print(f"   🔍 Searching web for: {query}")
        results = do_web_search(query)
        if results:
            print(f"   📄 Search results preview: {results[:100]}...")
        return results
    
    return None

def do_web_search(query, max_results=3):
    """Perform a web search and return formatted results."""
    if not SEARCH_AVAILABLE:
        return None
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            print("   ⚠️  No search results found")
            return None
        
        formatted = []
        for r in results:
            formatted.append(f"- {r.get('title', 'No title')}: {r.get('body', 'No description')}")
        
        result_text = "\n".join(formatted)
        print(f"   ✅ Found {len(results)} search results")
        return result_text
    
    except Exception as e:
        print(f"   ❌ Search error: {e}")
        return None

def send_reply(to_email, original_subject, reply_body):
    """Send a reply email."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = to_email
        
        # Add Re: if not already there
        if not original_subject.lower().startswith("re:"):
            subject = f"Re: {original_subject}"
        else:
            subject = original_subject
        msg["Subject"] = subject
        
        html_body = f"""
        <html>
        <body style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                        padding: 15px; border-radius: 10px 10px 0 0; color: white;">
                <h3 style="margin: 0;">🤖 AI Auto-Reply</h3>
            </div>
            <div style="padding: 20px; background: #f9f9f9; border-radius: 0 0 10px 10px;">
                <div style="font-size: 16px; line-height: 1.6;">
                    {reply_body.replace(chr(10), '<br>')}
                </div>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #888; font-size: 11px; text-align: center;">
                    This reply was generated by an AI assistant powered by Mistral.<br>
                    Replied at {datetime.now().strftime('%I:%M %p on %B %d, %Y')}
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)
        
        print(f"📧 Reply sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Reply failed: {e}")
        return False

def check_and_reply_to_emails(memory):
    """Check for new emails and auto-reply to them."""
    global AGENT_START_TIME
    
    print("📬 Checking for emails to reply to...")
    emails = read_recent_emails(count=10, unread_only=True)
    
    if not emails:
        print("   No new emails.")
        return False
    
    replied_to = memory.get("replied_to", [])
    ignored_old = memory.get("ignored_old", [])  # Old emails we're ignoring
    replies_sent = 0
    
    for email_data in emails:
        email_id = email_data['id']
        
        # Skip if we already replied to this one
        if email_id in replied_to:
            continue
        
        # Skip if this is an old email from before agent started
        if email_id in ignored_old:
            continue
        
        # Check if email arrived after agent started
        try:
            from email.utils import parsedate_to_datetime
            email_date = parsedate_to_datetime(email_data['date'])
            
            if AGENT_START_TIME and email_date < AGENT_START_TIME:
                print(f"   ⏭️  Skipping old email: {email_data['subject'][:30]}...")
                ignored_old.append(email_id)
                continue
        except:
            # If we can't parse date, check if it was there at startup
            if email_id in ignored_old:
                continue
        
        sender = get_sender_email(email_data['from'])
        print(f"\n📨 New email from {sender}")
        print(f"   Subject: {email_data['subject']}")
        
        # Check if search is needed first
        search_results = None
        if SEARCH_AVAILABLE:
            search_results = check_and_search(email_data)
        
        # Generate reply with Mistral
        print("   🤔 Thinking of reply...")
        reply = generate_reply_with_context(email_data, search_results)
        
        if reply:
            print("   📤 Sending reply...")
            success = send_reply(sender, email_data['subject'], reply)
            
            if success:
                replied_to.append(email_id)
                replies_sent += 1
        
    # Save state
    memory["replied_to"] = replied_to[-100:]  # Keep last 100
    memory["ignored_old"] = ignored_old[-100:]
    save_memory(memory)
    
    if replies_sent > 0:
        print(f"\n✅ Sent {replies_sent} replies")
    return replies_sent > 0

# === MEMORY ===
def load_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {
        "fortunes_given": [],
        "emails_sent": 0,
        "last_activities": []
    }

def save_memory(memory):
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))

# === EMAIL FUNCTION ===
def send_email(subject, body):
    """Send an email via Gmail SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = EMAIL_CONFIG["recipient_email"]
        msg["Subject"] = subject
        
        # Add nice HTML formatting
        html_body = f"""
        <html>
        <body style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0;">🤖 Your AI Agent Says...</h2>
            </div>
            <div style="padding: 30px; background: #f9f9f9; border-radius: 0 0 10px 10px;">
                <div style="font-size: 18px; line-height: 1.6;">
                    {body.replace(chr(10), '<br>')}
                </div>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #888; font-size: 12px; text-align: center;">
                    Sent with 💜 by your Mistral agent at {datetime.now().strftime('%I:%M %p')}
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)
        
        print(f"📧 Email sent to {EMAIL_CONFIG['recipient_email']}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# === LLM INTERFACE ===
def call_llm(messages, max_tokens=512):
    try:
        response = requests.post(
            LMSTUDIO_URL,
            json={
                "messages": messages,
                "temperature": 0.9,
                "max_tokens": max_tokens
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LM Studio. Is it running?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# === CONTENT GENERATORS ===
def generate_fortune(memory):
    """Generate a fortune cookie."""
    recent = memory.get("fortunes_given", [])[-10:]
    
    prompt = f"""Generate a single fortune cookie message. Be creative, mysterious, wise, or funny.
Avoid these recent ones: {recent[-3:] if recent else 'none'}
Just the fortune, no quotes."""
    
    response = call_llm([{"role": "user", "content": prompt}])
    if response:
        fortune = response.strip().strip('"\'')
        memory.setdefault("fortunes_given", []).append(fortune)
        return fortune
    return None

def generate_joke(memory):
    """Generate a joke."""
    joke_types = ["pun", "one-liner", "dad joke", "clever observation"]
    
    prompt = f"""Tell me a {random.choice(joke_types)}. Keep it clean and clever. Just the joke."""
    return call_llm([{"role": "user", "content": prompt}])

def generate_quote(memory):
    """Generate an inspirational quote."""
    prompt = """Generate an inspirational, philosophical, or thought-provoking quote.
Attribute it to someone (real, fictional, or made up).
Format: "[quote]" — [person]"""
    return call_llm([{"role": "user", "content": prompt}])

def generate_fact(memory):
    """Generate an interesting fact."""
    today = datetime.now()
    prompt = f"""Share one interesting fact. It could be:
- A "this day in history" fact for {today.strftime('%B %d')}
- A random science fact
- An unusual animal fact
- A word origin

Just the fact, make it interesting."""
    return call_llm([{"role": "user", "content": prompt}])

def generate_shower_thought(memory):
    """Generate a shower thought."""
    prompt = """Generate a "shower thought" — a random, mildly profound observation about everyday life.
Just the thought, nothing else."""
    return call_llm([{"role": "user", "content": prompt}])

# === EMAIL CONTENT TYPES ===
def send_fortune_email(memory):
    """Send a fortune cookie email."""
    fortune = generate_fortune(memory)
    if fortune:
        subject = "🥠 Your Fortune Cookie"
        body = f"""<div style="font-size: 24px; text-align: center; padding: 20px; 
                    background: #fff8e7; border-radius: 10px; margin: 20px 0;">
            🥠
            <br><br>
            <em>"{fortune}"</em>
        </div>"""
        return send_email(subject, body)
    return False

def send_daily_digest(memory):
    """Send a digest with multiple fun things."""
    fortune = generate_fortune(memory) or "The fortune teller is resting..."
    joke = generate_joke(memory) or "The comedian is on break..."
    quote = generate_quote(memory) or "The philosopher is thinking..."
    fact = generate_fact(memory) or "The fact checker is busy..."
    
    subject = f"🌟 Your Daily Dose of Fun - {datetime.now().strftime('%B %d')}"
    body = f"""
    <h3>🥠 Fortune Cookie</h3>
    <p style="font-style: italic; font-size: 18px;">"{fortune}"</p>
    
    <h3>😄 Joke of the Day</h3>
    <p>{joke}</p>
    
    <h3>💭 Words of Wisdom</h3>
    <p>{quote}</p>
    
    <h3>🧠 Interesting Fact</h3>
    <p>{fact}</p>
    """
    return send_email(subject, body)

def send_quick_thought(memory):
    """Send just a quick shower thought."""
    thought = generate_shower_thought(memory)
    if thought:
        subject = "🚿 A Thought From Your AI"
        body = f"""<div style="font-size: 20px; text-align: center; padding: 30px;">
            💭
            <br><br>
            {thought}
        </div>"""
        return send_email(subject, body)
    return False

EMAIL_TYPES = {
    "fortune": send_fortune_email,
    "digest": send_daily_digest,
    "thought": send_quick_thought,
    "inbox": check_and_report_emails,
    "reply": check_and_reply_to_emails
}

# === AGENT DECISION ===
def decide_what_to_send(memory):
    """Decide what kind of email to send."""
    hour = datetime.now().hour
    
    # Always check for emails to reply to first (50% of the time)
    if random.random() < 0.5:
        return "reply"
    
    # Sometimes just summarize inbox
    if random.random() < 0.2:
        return "inbox"
    
    # Morning = digest, afternoon = fortune, evening = thought
    if 6 <= hour < 10:
        return "digest"
    elif 10 <= hour < 18:
        return "fortune"
    else:
        return "thought"

# === MAIN LOOP ===
def run_agent():
    global AGENT_START_TIME
    
    print("=" * 50)
    print("📧 EMAIL AGENT STARTING (Dual Heartbeat)")
    print(f"   Inbox check: every {INBOX_CHECK_INTERVAL // 60} minutes")
    print(f"   Outgoing mail: every {OUTGOING_INTERVAL // 60} minutes")
    print(f"   Sending to: {EMAIL_CONFIG['recipient_email']}")
    print("=" * 50)
    
    # Set start time - only reply to emails after this
    from datetime import timezone
    AGENT_START_TIME = datetime.now(timezone.utc)
    print(f"\n🕐 Agent started at {AGENT_START_TIME.strftime('%H:%M:%S')}")
    print("   Will only reply to NEW emails from now on")
    
    # Mark existing unread emails as "old" so we don't reply to them
    print("\n📋 Checking for existing unread emails to ignore...")
    memory = load_memory()
    existing_emails = read_recent_emails(count=50, unread_only=True)
    if existing_emails:
        ignored = memory.get("ignored_old", [])
        for e in existing_emails:
            if e['id'] not in ignored:
                ignored.append(e['id'])
        memory["ignored_old"] = ignored[-100:]
        save_memory(memory)
        print(f"   Ignoring {len(existing_emails)} existing unread email(s)")
    else:
        print("   No existing unread emails")
    
    print("\nPress Ctrl+C to stop\n")
    
    last_outgoing_time = time.time()  # Track when we last sent outgoing mail
    
    while True:
        try:
            now = time.time()
            print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Inbox check...")
            
            # Always check for replies on each loop
            check_and_reply_to_emails(memory)
            
            # Check if it's time to send outgoing mail (fortune, digest, etc.)
            time_since_outgoing = now - last_outgoing_time
            if time_since_outgoing >= OUTGOING_INTERVAL:
                print(f"\n🎉 Time for outgoing mail!")
                
                hour = datetime.now().hour
                if 6 <= hour < 10:
                    email_type = "digest"
                elif 10 <= hour < 18:
                    email_type = "fortune"
                else:
                    email_type = "thought"
                
                print(f"   Sending: {email_type}")
                
                if email_type in EMAIL_TYPES:
                    success = EMAIL_TYPES[email_type](memory)
                    if success:
                        memory["emails_sent"] = memory.get("emails_sent", 0) + 1
                        memory.setdefault("last_activities", []).append(email_type)
                        save_memory(memory)
                
                last_outgoing_time = now
            else:
                mins_until = (OUTGOING_INTERVAL - time_since_outgoing) // 60
                print(f"   Next outgoing mail in ~{mins_until} minutes")
            
            print(f"\n😴 Next inbox check in {INBOX_CHECK_INTERVAL // 60} minutes...")
            time.sleep(INBOX_CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 Agent shutting down!")
            save_memory(memory)
            break

# === TEST MODE ===
def test_email():
    """Send a test email."""
    print("🧪 Sending test fortune email...")
    memory = load_memory()
    send_fortune_email(memory)
    save_memory(memory)

def test_digest():
    """Send a full digest."""
    print("🧪 Sending test digest...")
    memory = load_memory()
    send_daily_digest(memory)
    save_memory(memory)

def test_inbox():
    """Check inbox and send summary."""
    print("🧪 Checking inbox...")
    memory = load_memory()
    check_and_report_emails(memory)
    save_memory(memory)

def test_reply():
    """Check for emails and auto-reply."""
    print("🧪 Checking for emails to reply to...")
    memory = load_memory()
    check_and_reply_to_emails(memory)
    save_memory(memory)

def test_search():
    """Test web search functionality."""
    if not SEARCH_AVAILABLE:
        print("❌ Web search not available. Install with: pip install ddgs")
        return
    
    print("🔍 Testing web search...\n")
    query = "weather Austin Texas"
    print(f"Query: {query}")
    results = do_web_search(query)
    if results:
        print(f"\nResults:\n{results}")
    else:
        print("\n❌ No results returned")

def list_emails():
    """Just list recent emails without sending anything."""
    print("📬 Reading recent emails...\n")
    emails = read_recent_emails(count=5, unread_only=False)
    
    if not emails:
        print("No emails found.")
        return
    
    for i, e in enumerate(emails, 1):
        print(f"{'='*50}")
        print(f"📧 Email {i}")
        print(f"   From: {e['from']}")
        print(f"   Subject: {e['subject']}")
        print(f"   Date: {e['date']}")
        print(f"   Preview: {e['body'][:200]}...")
    print(f"{'='*50}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "test":
            test_email()
        elif cmd == "digest":
            test_digest()
        elif cmd == "inbox":
            test_inbox()
        elif cmd == "reply":
            test_reply()
        elif cmd == "search":
            test_search()
        elif cmd == "list":
            list_emails()
        else:
            print("Usage: python fun_agent_email.py [test|digest|inbox|reply|search|list]")
            print("")
            print("  test   - Send a test fortune cookie email")
            print("  digest - Send a full daily digest")
            print("  inbox  - Check inbox and email a summary")
            print("  reply  - Check for emails and auto-reply")
            print("  search - Test web search functionality")
            print("  list   - Just list recent emails (no send)")
            print("")
            print("  (no args) - Run the agent loop")
    else:
        run_agent()
