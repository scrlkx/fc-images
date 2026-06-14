#!/usr/bin/env bash

set -euo pipefail

INSTALL_DIR="${1:?Usage: $0 <install-dir>}"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/fc-images-tool.desktop"

mkdir -p "$DESKTOP_DIR"
printf '[Desktop Entry]\nName=FC Images Tool\nExec=%s/run-app.sh\nIcon=%s/icon.png\nType=Application\nCategories=Graphics;ImageProcessing;\nTerminal=false\n' \
    "$INSTALL_DIR" "$INSTALL_DIR" > "$DESKTOP_FILE"

echo "Desktop shortcut installed: ${DESKTOP_FILE}"
