#!/usr/bin/env bash
# Wraps everything in main() so a partial curl download doesn't execute anything.
set -euo pipefail

REPO_URL="https://github.com/scrlkx/fc-images"
INSTALL_DIR="${HOME}/.local/share/fc-images"
BIN_DIR="${HOME}/.local/bin"
WRAPPER="${BIN_DIR}/fc-images"
EXT_DIR="${HOME}/.local/share/nautilus-python/extensions"
EXT_LINK="${EXT_DIR}/fc_images_nautilus.py"

main() {
    if [[ "${1:-}" == "--uninstall" ]]; then
        do_uninstall
        return
    fi

    echo "==> fc-images installer"
    echo ""

    check_prerequisites
    clone_or_update
    setup_venv
    install_wrapper
    install_nautilus_extension
    check_path
    print_summary
}

# ── Prerequisites ────────────────────────────────────────────────────────────

check_prerequisites() {
    local ok=true

    if ! command -v git &>/dev/null; then
        echo "ERROR: git is not installed." >&2
        ok=false
    fi

    # Use system python3, not whatever is on PATH (could be a venv)
    local python
    python=$(find_python3) || {
        echo "ERROR: python3 >= 3.10 is required." >&2
        ok=false
    }

    if [[ "$ok" == false ]]; then
        exit 1
    fi

    export PYTHON3="$python"
    echo "  python3: $PYTHON3 ($("$PYTHON3" --version 2>&1))"
}

find_python3() {
    local candidates=("${PYTHON3:-}" /usr/bin/python3 /usr/local/bin/python3 python3)
    for py in "${candidates[@]}"; do
        [[ -z "$py" ]] && continue
        if command -v "$py" &>/dev/null; then
            local ver
            ver=$("$py" -c "import sys; print(sys.version_info[:2])" 2>/dev/null) || continue
            if "$py" -c "import sys; assert sys.version_info >= (3,10)" 2>/dev/null; then
                echo "$py"
                return 0
            fi
        fi
    done
    return 1
}

# ── Clone / Update ───────────────────────────────────────────────────────────

clone_or_update() {
    if [[ -d "${INSTALL_DIR}/.git" ]]; then
        echo "==> Updating existing installation..."
        git -C "$INSTALL_DIR" pull --ff-only
    else
        echo "==> Cloning repository..."
        mkdir -p "$(dirname "$INSTALL_DIR")"
        git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
    fi
}

# ── Venv + Dependencies ──────────────────────────────────────────────────────

setup_venv() {
    local venv="${INSTALL_DIR}/.venv"
    local req="${INSTALL_DIR}/requirements.txt"
    local hash_file="${INSTALL_DIR}/.installed-requirements-hash"

    if [[ ! -d "$venv" ]]; then
        echo "==> Creating virtual environment..."
        "$PYTHON3" -m venv "$venv"
    fi

    local current_hash
    current_hash=$(sha256sum "$req" | cut -d' ' -f1)
    local stored_hash=""
    [[ -f "$hash_file" ]] && stored_hash=$(cat "$hash_file")

    if [[ "$current_hash" != "$stored_hash" ]]; then
        echo "==> Installing Python dependencies (this may take a minute)..."
        "$venv/bin/pip" install --upgrade pip --quiet
        "$venv/bin/pip" install -r "$req"
        echo "$current_hash" > "$hash_file"
    else
        echo "==> Dependencies already up to date."
    fi
}

# ── fc-images wrapper ────────────────────────────────────────────────────────

install_wrapper() {
    mkdir -p "$BIN_DIR"
    cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
exec "${INSTALL_DIR}/.venv/bin/python" \\
     "${INSTALL_DIR}/convert_images.py" \\
     "\$@"
EOF
    chmod +x "$WRAPPER"
    echo "==> Installed: fc-images -> ${WRAPPER}"
}

# ── Nautilus extension ───────────────────────────────────────────────────────

install_nautilus_extension() {
    if ! command -v nautilus &>/dev/null; then
        echo "==> Nautilus not found — skipping file manager extension."
        echo "    (fc-images CLI is still available)"
        return
    fi

    if ! "$PYTHON3" -c "import gi; gi.require_version('Nautilus', '4.1')" 2>/dev/null; then
        echo ""
        echo "WARNING: nautilus-python is not installed."
        echo "  The right-click extension requires it. Install with:"
        if command -v dnf &>/dev/null; then
            echo "    sudo dnf install nautilus-python"
        elif command -v apt-get &>/dev/null; then
            echo "    sudo apt install python3-nautilus"
        elif command -v pacman &>/dev/null; then
            echo "    sudo pacman -S python-nautilus"
        else
            echo "    (install the nautilus-python package for your distro)"
        fi
        echo "  Then re-run this installer."
        return
    fi

    mkdir -p "$EXT_DIR"
    ln -sf "${INSTALL_DIR}/nautilus_extension.py" "$EXT_LINK"
    echo "==> Installed Nautilus extension: ${EXT_LINK}"

    if pgrep -x nautilus &>/dev/null; then
        nautilus -q 2>/dev/null || true
        echo "==> Nautilus restarted."
    fi
}

# ── PATH check ───────────────────────────────────────────────────────────────

check_path() {
    if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
        echo ""
        echo "WARNING: ${BIN_DIR} is not on your PATH."
        echo "  Add this to your ~/.bashrc or ~/.zshrc:"
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "  Then restart your shell or run: source ~/.bashrc"
    fi
}

# ── Summary ──────────────────────────────────────────────────────────────────

print_summary() {
    echo ""
    echo "Done!"
    echo ""
    echo "  fc-images <directory>               — convert formats + remove backgrounds"
    echo "  fc-images <directory> --keep-background  — convert formats only"
    echo "  fc-images <directory> --backgrounds-only — remove backgrounds only"
    echo ""
    echo "NOTE: The first run will download the birefnet-general AI model (~1 GB)."
    echo "      This is a one-time download cached in ~/.u2net/."
}

# ── Uninstall ────────────────────────────────────────────────────────────────

do_uninstall() {
    echo "==> Uninstalling fc-images..."

    [[ -f "$WRAPPER" ]] && rm -f "$WRAPPER" && echo "  Removed: ${WRAPPER}"
    [[ -L "$EXT_LINK" ]] && rm -f "$EXT_LINK" && echo "  Removed: ${EXT_LINK}"

    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        echo "  Removed: ${INSTALL_DIR}"
    fi

    echo ""
    echo "Uninstalled."
    echo ""
    echo "NOTE: The AI model cache (~1 GB) was left in place at ~/.u2net/"
    echo "      Remove it manually if you no longer need it:"
    echo "        rm -rf ~/.u2net"
}

main "$@"
