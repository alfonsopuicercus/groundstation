"""
Ollama plugin — local model management.
Configure via .env:
  OLLAMA_MODELS_PATH   where models are stored (e.g. on LaCie)
"""

import os, subprocess
from pathlib import Path

MODELS_PATH = os.environ.get("OLLAMA_MODELS_PATH", str(Path.home() / ".ollama" / "models"))

def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def status():
    server = bool(sh("pgrep -f 'ollama serve'"))
    pulling = sh("pgrep -f 'ollama pull'")
    models = sh(f'OLLAMA_MODELS="{MODELS_PATH}" ollama list 2>/dev/null | tail -n +2')
    lines = [f"  {l.split()[0]}" for l in models.splitlines() if l.strip()] if models else ["  none"]
    state = "server running" if server else "server stopped"
    if pulling:
        state += ", pull in progress"
    return f"*Ollama ({state})*\n" + "\n".join(lines)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ollama_pull",
            "description": "Download an Ollama model to the configured models path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "e.g. llama3.1:8b, qwen2.5:7b"}
                },
                "required": ["model"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ollama_list",
            "description": "List all downloaded Ollama models.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

def execute_tool(name, args):
    if name == "ollama_pull":
        model = args.get("model", "")
        if not model:
            return "Specify a model name."
        subprocess.Popen(
            f'OLLAMA_MODELS="{MODELS_PATH}" ollama serve >/dev/null 2>&1; '
            f'OLLAMA_MODELS="{MODELS_PATH}" ollama pull {model}',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return f"Pulling `{model}` in background → `{MODELS_PATH}`"
    if name == "ollama_list":
        return status()
    return f"Unknown tool: {name}"
