#!/bin/bash
# Reusable Telegram notifier. Source this in any script:
#   source "$(dirname "$0")/nemoclaw_notify.sh"
# Or from anywhere if the repo is at ~/Desktop/alfonso-assistant:
#   source ~/Desktop/alfonso-assistant/nemoclaw_notify.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        export "$key"="${value}"
    done < "$SCRIPT_DIR/../.env"
fi

TG_TOKEN="${TELEGRAM_TOKEN}"
TG_CHAT_ID="${TELEGRAM_CHAT_ID}"

tg_notify() {
    local msg="$1"
    curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\": \"${TG_CHAT_ID}\", \"text\": \"${msg}\", \"parse_mode\": \"Markdown\"}" \
        > /dev/null
}
