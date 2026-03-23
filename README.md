# Groundstation

A lightweight, plugin-based Telegram bot that acts as a personal command centre for your Mac or PC. Control background jobs, monitor system state, run scripts, and chat with a local or cloud LLM — all from Telegram.

Built around a minimal core and a simple plugin interface, so you can drop in new capabilities without touching the framework.

---

## How it works

```
Telegram
   │
   ├─ /status          → snapshot from all plugins
   ├─ /do <anything>   → Nemotron parses intent → calls plugin tools
   ├─ /agent <task>    → full NemoClaw sandbox agent (multi-step)
   └─ free text        → LLM Q&A
```

Any script can also push notifications to Telegram by sourcing `core/notify.sh`.

---

## Commands

| Command | Description |
|---|---|
| `/status` | Snapshot from all loaded plugins |
| `/do <task>` | Natural language action — AI picks the right tool |
| `/agent <task>` | Routes to a NemoClaw OpenClaw sandbox agent |
| free text | Q&A via Nemotron (or any OpenAI-compatible model) |

---

## Plugins

| Plugin | What it adds |
|---|---|
| `system.py` | CPU usage, job monitoring, generic `shell` tool |
| `photos.py` | iCloud photo export via osxphotos — progress, start/stop |
| `ollama.py` | Local model management — pull, list |
| `zotero.py` | Zotero paper analysis pipeline — status, start |

Drop a new `.py` file into `plugins/` and it's picked up automatically on next start.

---

## Plugin interface

Each plugin is a plain Python module. All fields are optional — implement only what you need.

```python
# plugins/myplugin.py

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "my_action",
            "description": "Does something useful.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "..."}
                },
                "required": ["input"],
            },
        },
    }
]

def status() -> str:
    # Included in /status output. Return "" to skip.
    return "*My plugin* — everything nominal"

def execute_tool(name: str, args: dict) -> str:
    if name == "my_action":
        return f"Did something with {args['input']}"
```

---

## Setup

### Requirements
- Python 3.11+
- An [NVIDIA API key](https://build.nvidia.com) for Nemotron (cloud inference)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Mac / Linux

```bash
git clone https://github.com/alfonsopuicercus/groundstation.git
cd groundstation
cp .env.example .env
# fill in .env with your credentials
bash setup_mac.sh
```

`setup_mac.sh` creates a venv, installs dependencies, and registers a LaunchAgent so the bot starts on login and restarts on crash.

### Windows

See [SETUP_WINDOWS.md](SETUP_WINDOWS.md) for step-by-step instructions including Ollama + GPU setup.

---

## Configuration

All configuration lives in `.env` (never committed). See `.env.example` for all options.

```env
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
NVIDIA_API_KEY=...

# Plugin-specific (optional)
LACIE_PHOTOS=/Volumes/LaCie/photos icloud
PHOTO_EXPORT_TOTAL=19132
OLLAMA_MODELS_PATH=/Volumes/LaCie/ollama-models
ZOTERO_RESULTS_DIR=~/Desktop/zotero_analysis_results

# Override the system prompt for Q&A
SYSTEM_PROMPT=You are a helpful assistant...

# Jobs to monitor in /status (label:pgrep_pattern,...)
GROUNDSTATION_JOBS=Photo export:osxphotos,Ollama:ollama serve
```

---

## Stack

- **[Nemotron](https://build.nvidia.com)** — cloud LLM for Q&A and tool-use (`/do`)
- **[NemoClaw](https://github.com/NVIDIA/NemoClaw)** — sandboxed agent runtime for `/agent`
- **[Ollama](https://ollama.com)** — local model serving
- **[osxphotos](https://github.com/RhetTbull/osxphotos)** — iCloud photo export (photos plugin)

---

## Notifications from any script

Source `core/notify.sh` in any shell script to send a Telegram message:

```bash
source ~/groundstation/core/notify.sh
tg_notify "Backup finished."
```

---

## License

MIT
