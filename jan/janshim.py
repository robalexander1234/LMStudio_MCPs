import json, requests, uuid, time, re
from flask import Flask, request, Response

app = Flask(__name__)
FLM_URL = "http://127.0.0.1:52625/v1/chat/completions"

# ---- TUNING ----
MAX_SEARCH_RESULTS = 3
MAX_FETCH_CHARS = 2000
MAX_HISTORY_TURNS = 2       # Keep last N user/assistant pairs (0 = unlimited)
MAX_HISTORY_RESPONSE = 150  # Max chars to keep from each assistant response in history
# -----------------

# Store assistant responses for item_reference replay
response_store = {}


def extract_content(item):
    """Robustly extract text from any format Jan might send."""
    content = item.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
        return "".join(parts).strip()
    return ""


def web_search(query):
    """Search DuckDuckGo and return top results."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS))
        if not results:
            return f"[No results found for: {query}]"
        text = f"Web search results for: {query}\n\n"
        for i, r in enumerate(results, 1):
            text += f"{i}. {r.get('title', 'No title')}\n"
            text += f"   {r.get('href', '')}\n"
            text += f"   {r.get('body', '')}\n\n"
        return text
    except ImportError:
        return "[Error: ddgs not installed. Run: pip install ddgs]"
    except Exception as e:
        return f"[Search error: {e}]"


def fetch_url(url):
    """Fetch a URL and extract readable text."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "[Error: beautifulsoup4 not installed. Run: pip install beautifulsoup4]"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # If JSON, return it directly
        content_type = resp.headers.get("content-type", "")
        if "json" in content_type:
            return f"Content from {url}:\n\n{resp.text[:MAX_FETCH_CHARS]}"

        # Otherwise parse HTML
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return f"Content from {url}:\n\n{text[:MAX_FETCH_CHARS]}"
    except Exception as e:
        return f"[Fetch error for {url}: {e}]"


def process_commands(user_text):
    """Check for /search and /fetch commands. Returns (cleaned_text, injected_context)."""
    context_parts = []
    cleaned = user_text

    # Handle /search <query>
    search_match = re.match(r'^/search\s+(.+)', user_text, re.IGNORECASE)
    if search_match:
        query = search_match.group(1).strip()
        print(f"  [SEARCH] Querying: {query}")
        result = web_search(query)
        context_parts.append(result)
        cleaned = f"Based on the search results below, answer my question: {query}"

    # Handle /fetch <url>
    fetch_match = re.match(r'^/fetch\s+(https?://\S+)', user_text, re.IGNORECASE)
    if fetch_match:
        url = fetch_match.group(1).strip()
        print(f"  [FETCH] Fetching: {url}")
        result = fetch_url(url)
        context_parts.append(result)
        cleaned = f"Based on the content below, summarize or answer questions about this page: {url}"

    if context_parts:
        context_block = "\n\n---\n".join(context_parts)
        return cleaned, context_block
    return user_text, None


@app.route('/v1/responses', methods=['POST'])
def proxy():
    jan_data = request.json
    res_id = f"res_{uuid.uuid4().hex[:12]}"
    item_id = f"msg_{uuid.uuid4().hex[:12]}"

    # --- Build clean message list for FLM ---
    history = []

    for item in jan_data.get("input", []):
        if item.get("type") == "item_reference":
            ref_id = item.get("id", "")
            stored_text = response_store.get(ref_id, "")
            if stored_text:
                # Truncate long responses to keep prefill fast
                if MAX_HISTORY_RESPONSE > 0 and len(stored_text) > MAX_HISTORY_RESPONSE:
                    stored_text = stored_text[:MAX_HISTORY_RESPONSE] + "..."
                history.append({"role": "assistant", "content": stored_text})
            continue

        role = item.get("role", "user")
        if role == "system":
            continue

        text = extract_content(item)
        if text:
            history.append({"role": role, "content": text})

    # Trim to last N turns (a turn = one user + one assistant message)
    if MAX_HISTORY_TURNS > 0 and len(history) > MAX_HISTORY_TURNS * 2:
        history = history[-(MAX_HISTORY_TURNS * 2):]

    # Handle /flush — drop all history, keep only the question after it
    if history and history[-1]["role"] == "user":
        flush_match = re.match(r'^/flush\s*(.*)', history[-1]["content"], re.IGNORECASE)
        if flush_match:
            question = flush_match.group(1).strip()
            if question:
                history = [{"role": "user", "content": question}]
                print("  [FLUSH] History cleared, keeping question")
            else:
                history = [{"role": "user", "content": "Hello!"}]
                print("  [FLUSH] History cleared")

    # Process commands on the LAST user message
    injected_context = None
    if history and history[-1]["role"] == "user":
        processed_text, injected_context = process_commands(history[-1]["content"])
        history[-1]["content"] = processed_text

    # Build final messages
    system_content = "You are a helpful assistant. /no_think"
    if injected_context:
        system_content += f"\n\nReference material:\n{injected_context}"

    cleaned_messages = [{"role": "system", "content": system_content}] + history

    # Debug: show context size per message
    total_chars = sum(len(m["content"]) for m in cleaned_messages)
    print(f"  [CONTEXT] {len(cleaned_messages)} messages, ~{total_chars} chars")
    for i, m in enumerate(cleaned_messages):
        print(f"    [{i}] {m['role']}: {len(m['content'])} chars - {m['content'][:60]}...")

    def generate():
        yield f"data: {json.dumps({'type': 'response.created', 'id': res_id})}\n\n".encode()
        yield f"data: {json.dumps({'type': 'response.output_item.added', 'output_index': 0, 'item': {'id': item_id, 'type': 'message', 'role': 'assistant', 'status': 'in_progress', 'content': []}})}\n\n".encode()

        payload = {
            "model": "qwen3:4b",
            "messages": cleaned_messages,
            "stream": True,
            "temperature": 0.7
        }

        full_response = []
        token_count = 0
        t_start = time.perf_counter()
        t_first = None

        with requests.post(FLM_URL, json=payload, stream=True) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                decoded = line.decode('utf-8').replace('data: ', '')
                if decoded.strip() == '[DONE]':
                    break
                try:
                    chunk = json.loads(decoded)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        if t_first is None:
                            t_first = time.perf_counter()
                        token_count += 1
                        full_response.append(content)
                        yield f"data: {json.dumps({'type': 'response.output_text.delta', 'item_id': item_id, 'output_index': 0, 'content_index': 0, 'delta': content})}\n\n".encode()
                except:
                    continue

        t_end = time.perf_counter()

        # Calculate stats
        total_time = t_end - t_start
        gen_time = t_end - t_first if t_first else total_time
        ttft = (t_first - t_start) if t_first else 0
        tps = token_count / gen_time if gen_time > 0 else 0

        stats_line = f"\n\n---\n📊 {token_count} tokens | {tps:.1f} t/s | TTFT {ttft:.2f}s | Total {total_time:.2f}s"

        yield f"data: {json.dumps({'type': 'response.output_text.delta', 'item_id': item_id, 'output_index': 0, 'content_index': 0, 'delta': stats_line})}\n\n".encode()

        # Store response WITHOUT stats for clean history replay
        response_store[item_id] = "".join(full_response)

        yield f"data: {json.dumps({'type': 'response.output_item.done', 'output_index': 0, 'item': {'id': item_id, 'status': 'completed', 'content': [{'type': 'output_text', 'text': ''}]}})}\n\n".encode()
        yield b"data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("--- Jan-to-FLM Bridge Active (v6 - search, fetch, flush) ---")
    print("Commands:")
    print("  /search <query>  - Search the web via DuckDuckGo")
    print("  /fetch <url>     - Fetch and read a web page")
    print("  /flush <question> - Clear history, ask fresh question")
    print()
    app.run(port=5000)
