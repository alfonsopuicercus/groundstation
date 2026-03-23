"""
Zotero plugin — paper analysis pipeline status and control.
Configure via .env:
  ZOTERO_RESULTS_DIR   path to analysis results directory
  ZOTERO_ANALYSIS_CMD  command to run the analysis script
"""

import os, subprocess
from pathlib import Path

RESULTS_DIR  = Path(os.environ["ZOTERO_RESULTS_DIR"]) if os.environ.get("ZOTERO_RESULTS_DIR") else None
ANALYSIS_CMD = os.environ.get("ZOTERO_ANALYSIS_CMD", "")

def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def status():
    if not RESULTS_DIR or not RESULTS_DIR.exists():
        return ""
    files = list(RESULTS_DIR.glob("*.md"))
    prefixes = ("CROSS", "CLAIM", "INDEX", "METHOD", "SUMMARY")
    reports = [f.name for f in files if any(f.name.startswith(p) for p in prefixes) or f.name.isupper()]
    papers = len([f for f in files if f.name not in reports and f.name != "INDEX.md"])
    running = bool(sh("pgrep -f zotero_analysis"))
    state = "running" if running else "idle"
    return f"*Zotero ({state})* — {papers} papers analysed, {len(reports)} reports"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "zotero_analysis_start",
            "description": "Start the Zotero paper analysis pipeline.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

def execute_tool(name, args):
    if name == "zotero_analysis_start":
        if not ANALYSIS_CMD:
            return "Set ZOTERO_ANALYSIS_CMD in .env to enable this."
        subprocess.Popen(ANALYSIS_CMD, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Zotero analysis started."
    return f"Unknown tool: {name}"
