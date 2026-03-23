#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/core/notify.sh"

DEST="${LACIE_PHOTOS:?Set LACIE_PHOTOS in .env}"
TOTAL="${PHOTO_EXPORT_TOTAL:-0}"

current_count() { find "$DEST" -type f | wc -l | tr -d ' '; }

if [ ! -d "$DEST" ]; then
    tg_notify "Photo export failed: LaCie not mounted."
    echo "LaCie not mounted at $DEST"; exit 1
fi

ALREADY=$(current_count)
echo "Resuming photo export — $ALREADY / $TOTAL already exported."
tg_notify "Photo export started. Progress: $ALREADY / $TOTAL files on LaCie."

(
    while true; do
        sleep 300
        NOW=$(current_count)
        tg_notify "Photo export progress: $NOW / $TOTAL files on LaCie."
    done
) &
PROGRESS_PID=$!

${OSXPHOTOS_BIN:-osxphotos} export "$DEST" --download-missing --skip-edited --update
EXIT_CODE=$?
kill $PROGRESS_PID 2>/dev/null

FINAL=$(current_count)
if [ $EXIT_CODE -eq 0 ]; then
    tg_notify "Photo export finished. $FINAL / $TOTAL files on LaCie."
    echo "Export finished! $FINAL total files."
else
    tg_notify "Photo export ended with errors (exit $EXIT_CODE). $FINAL / $TOTAL files on LaCie."
    echo "Export ended with errors. $FINAL total files."
fi
