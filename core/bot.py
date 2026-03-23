#!/usr/bin/env python3
"""
Groundstation — core bot engine.
Loads all plugins from ../plugins/ and wires them into /status, /do, /agent, and Q&A.
"""

import os, sys, json, requests, time, subprocess, tempfile, importlib.util
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

TOKEN      = os.environ["TELEGRAM_TOKEN"]
NVIDIA_KEY = os.environ["NVIDIA_API_KEY"]
MODEL      = os.environ.get("NEMOTRON_MODEL", "nvidia/nemotron-3-super-120b-a12b")
NC_SANDBOX  = os.environ.get("NEMOCLAW_SANDBOX", "my-assistant")
NC_BIN      = os.environ.get("NEMOCLAW_BIN", str(Path.home() / ".nemoclaw/source/bin/nemoclaw.js"))

NVIDIA_HEADERS = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"}

SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    "You are a personal AI assistant controlling a Mac/PC via Telegram. "
    "Answer concisely. Use tools when the user wants action taken.",
)

conversation_history = {}

# ── Plugin loader ─────────────────────────────────────────────────

def load_plugins():
    plugins = []
    plugin_dir = ROOT / "plugins"
    for path in sorted(p for p in plugin_dir.glob("*.py") if p.stem != "__init__"):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        plugins.append(mod)
        print(f"  loaded plugin: {path.stem}", flush=True)
    return plugins

PLUGINS = []

def get_tools():
    tools = []
    for p in PLUGINS:
        tools.extend(getattr(p, "TOOLS", []))
    return tools

def dispatch_tool(name, args):
    for p in PLUGINS:
        if hasattr(p, "execute_tool") and name in [t["function"]["name"] for t in getattr(p, "TOOLS", [])]:
            return p.execute_tool(name, args)
    return f"No plugin handles tool: {name}"

def get_status():
    parts = []
    for p in PLUGINS:
        if hasattr(p, "status"):
            s = p.status()
            if s:
                parts.append(s)
    return "\n\n".join(parts) if parts else "Nothing to report."

# ── Telegram ──────────────────────────────────────────────────────

def tg_get(method, **params):
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/{method}", params=params, timeout=10)
    return r.json()

def tg_send(chat_id, text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text[i:i+4000], "parse_mode": "Markdown"},
            timeout=10,
        )
        time.sleep(0.3)

# ── /do — tool-use ────────────────────────────────────────────────

def cmd_do(arg):
    if not arg.strip():
        return "Tell me what to do, e.g. `/do start the photo export` or `/do how much disk is free`"
    tools = get_tools()
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=NVIDIA_HEADERS,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": arg},
                ],
                "tools": tools,
                "max_tokens": 500,
                "temperature": 0.2,
            },
            timeout=60,
        )
        r.raise_for_status()
        choice = r.json()["choices"][0]["message"]
        if choice.get("tool_calls"):
            return "\n\n".join(
                dispatch_tool(tc["function"]["name"], json.loads(tc["function"].get("arguments", "{}")))
                for tc in choice["tool_calls"]
            )
        return choice.get("content", "Done.").strip()
    except Exception as e:
        return f"Error: {e}"

# ── /agent — NemoClaw sandbox ─────────────────────────────────────

def cmd_agent(arg):
    if not arg.strip():
        return "Usage: `/agent <task>` — routes to the NemoClaw OpenClaw sandbox agent."
    try:
        ssh_config = subprocess.check_output(
            ["node", NC_BIN, NC_SANDBOX, "ssh-config"],
            text=True, stderr=subprocess.DEVNULL, timeout=10,
        )
    except Exception as e:
        return f"Sandbox SSH config failed: {e}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(ssh_config)
        conf = f.name
    os.chmod(conf, 0o600)

    safe = arg.replace("'", "'\\''")
    remote_cmd = (
        f"export NVIDIA_API_KEY='{NVIDIA_KEY}' && "
        f"nemoclaw-start openclaw agent --agent main --local -m '{safe}' --session-id tg-agent"
    )
    try:
        out = subprocess.check_output(
            ["ssh", "-T", "-F", conf, f"openshell-{NC_SANDBOX}", remote_cmd],
            text=True, stderr=subprocess.DEVNULL, timeout=120,
        )
        skip = ("Setting up NemoClaw", "[plugins]", "(node:", "NemoClaw ready",
                "NemoClaw registered", "openclaw agent", "┌─", "│ ", "└─")
        lines = [l for l in out.splitlines() if l.strip() and not any(l.startswith(s) for s in skip)]
        return "\n".join(lines).strip() or "(no response)"
    except subprocess.TimeoutExpired:
        return "Agent timed out (>2 min)."
    except Exception as e:
        return f"Agent error: {e}"
    finally:
        try: os.unlink(conf)
        except: pass

# ── Q&A ───────────────────────────────────────────────────────────

def ask(chat_id, text):
    history = conversation_history.setdefault(chat_id, [])
    history.append({"role": "user", "content": text})
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=NVIDIA_HEADERS,
            json={
                "model": MODEL,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:],
                "max_tokens": 1000,
                "temperature": 0.3,
            },
            timeout=60,
        )
        r.raise_for_status()
        reply = (r.json()["choices"][0]["message"].get("content") or "...").strip()
        history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"Error: {e}"

# ── Dispatch ──────────────────────────────────────────────────────

HELP = (
    "*Groundstation*\n\n"
    "`/status` — system snapshot\n"
    "`/do <task>` — take an action (natural language)\n"
    "`/agent <task>` — NemoClaw sandbox for complex tasks\n\n"
    "Or just ask anything."
)

def handle(update):
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").strip()
    if not chat_id or not text:
        return
    print(f"[{chat_id}] {text[:80]}", flush=True)
    low = text.lower()

    if low in ("/start", "/help"):
        tg_send(chat_id, HELP)
    elif low == "/status":
        tg_send(chat_id, get_status())
    elif low.startswith("/do"):
        tg_send(chat_id, "⏳ On it...")
        tg_send(chat_id, cmd_do(text[3:].strip()))
    elif low.startswith("/agent"):
        tg_send(chat_id, "⏳ Routing to NemoClaw agent...")
        tg_send(chat_id, cmd_agent(text[6:].strip()))
    else:
        tg_send(chat_id, "⏳ Thinking...")
        tg_send(chat_id, ask(chat_id, text))

# ── Main ──────────────────────────────────────────────────────────

def main():
    global PLUGINS
    print("Groundstation starting...", flush=True)
    PLUGINS = load_plugins()
    print(f"  {len(PLUGINS)} plugin(s) loaded.", flush=True)

    offset = None
    while True:
        try:
            result = tg_get("getUpdates", offset=offset, timeout=30)
            for update in result.get("result", []):
                offset = update["update_id"] + 1
                handle(update)
        except Exception as e:
            print(f"Poll error: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
