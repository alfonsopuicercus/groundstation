#!/bin/bash
set -e
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Alfonso Assistant Setup (Mac) ==="

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
chmod +x "$REPO_DIR/nemoclaw_notify.sh" "$REPO_DIR/resume_photo_export.command"

# 4. Install LaunchAgent (auto-start bot on login)
PLIST="$REPO_DIR/launchagent/com.alfonso.telegrambot.plist"
sed "s|__REPO__|$REPO_DIR|g" "$PLIST.template" > ~/Library/LaunchAgents/com.alfonso.telegrambot.plist
launchctl unload ~/Library/LaunchAgents/com.alfonso.telegrambot.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.alfonso.telegrambot.plist
echo "Bot LaunchAgent loaded — will start on login and restart if it crashes."

# 5. Update ~/.nemoclaw_notify.sh symlink for backwards compatibility
ln -sf "$REPO_DIR/nemoclaw_notify.sh" ~/.nemoclaw_notify.sh

echo ""
echo "Done. Bot is running. Check Telegram."
