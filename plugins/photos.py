"""
Photos plugin — iCloud photo export to an external drive via osxphotos.
Configure via .env:
  LACIE_PHOTOS    path to export destination
  PHOTO_EXPORT_TOTAL  expected total photo count
  PHOTO_EXPORT_CMD    full osxphotos command (optional override)
"""

import os, subprocess
from pathlib import Path

DEST        = Path(os.environ["LACIE_PHOTOS"]) if os.environ.get("LACIE_PHOTOS") else None
TOTAL       = int(os.environ.get("PHOTO_EXPORT_TOTAL", "0"))
EXPORT_CMD  = os.environ.get(
    "PHOTO_EXPORT_CMD",
    f'bash "{Path(__file__).parent.parent / "resume_photo_export.command"}"',
)

def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def _count():
    if not DEST or not DEST.exists():
        return None
    return int(sh(f'find "{DEST}" -type f | wc -l'))

def status():
    if not DEST:
        return ""   # plugin inactive — LACIE_PHOTOS not set
    count = _count()
    if count is None:
        return "*Photos* — destination not mounted"
    pct = count / TOTAL * 100
    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    state = "running" if sh("pgrep -f osxphotos") else "stopped"
    return f"*Photos ({state})*\n`{bar}` {pct:.1f}%\n{count:,} / {TOTAL:,}"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "photo_export_start",
            "description": "Start or resume the photo export to the external drive.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "photo_export_stop",
            "description": "Stop the photo export.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

def execute_tool(name, args):
    if name == "photo_export_start":
        subprocess.Popen(EXPORT_CMD, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Photo export started."
    if name == "photo_export_stop":
        sh("pkill -f osxphotos")
        return "Photo export stopped."
    return f"Unknown tool: {name}"
