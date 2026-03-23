"""
System plugin — generic Mac/Linux monitoring and shell access.
Provides /status info (CPU, jobs) and the shell tool for /do.
"""

import os, subprocess
from pathlib import Path

# Jobs to monitor: list of (label, pgrep pattern) from env or defaults
_RAW = os.environ.get("GROUNDSTATION_JOBS", "")
JOBS = (
    [tuple(j.split(":", 1)) for j in _RAW.split(",") if ":" in j]
    if _RAW else []
)

def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def sh_bg(cmd):
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def status():
    parts = []

    # CPU
    cpu = sh("ps -A -o %cpu | awk '{s+=$1} END {printf \"%.0f\", s}'")
    parts.append(f"*System* — CPU {cpu}%")

    # Configured jobs
    if JOBS:
        lines = [f"{'✅' if sh(f'pgrep -f \"{p}\"') else '⬜'} {l}" for l, p in JOBS]
        parts.append("*Jobs*\n" + "\n".join(lines))

    return "\n\n".join(parts)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "shell",
            "description": "Run a shell command on the host machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_status",
            "description": "Get the current system status including all running jobs and resources.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

def execute_tool(name, args):
    if name == "shell":
        cmd = args.get("command", "")
        out = sh(cmd)
        return f"`{cmd}`\n```\n{out[:1500]}\n```" if out else f"Ran `{cmd}` — no output."
    if name == "get_status":
        from core.bot import get_status
        return get_status()
    return f"Unknown tool: {name}"
