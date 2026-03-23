#!/bin/bash
set -e
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="${GROUNDSTATION_LABEL:-com.groundstation.bot}"

echo "=== Groundstation Setup (Mac) ==="

# 1. Check .env
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo "Created .env from template — fill in your credentials, then re-run."
    exit 1
fi

# 2. Python venv + deps
python3 -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/pip" install -r "$REPO_DIR/requirements.txt" --quiet

# 3. Make scripts executable
chmod +x "$REPO_DIR/core/notify.sh" "$REPO_DIR/resume_photo_export.command"

# 4. Install LaunchAgent (auto-start on login, restart on crash)
PLIST_DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"
sed "s|__REPO__|$REPO_DIR|g; s|__LABEL__|$LABEL|g" \
    "$REPO_DIR/launchagent/com.groundstation.bot.plist.template" > "$PLIST_DEST"
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo ""
echo "Done. Bot is running as '$LABEL'. Check Telegram."
