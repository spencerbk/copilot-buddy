#!/bin/bash
# ============================================================
# open-copilot.sh
#
# Double-click or run from shell to open an LXTerminal window
# for this repo with GitHub Copilot CLI running.
#
# On first run, also installs .desktop shortcuts on the Desktop
# and in the application menu.
#
# Targets Raspberry Pi OS (Trixie / Debian 13) with LXTerminal.
#
# To use in another repo: copy this file to <repo>/scripts/
# and change only TAB_COLOR below.
# ============================================================

# -----------------------------------------------------------
# User-configurable: tab color (hex). Change per repo.
# (Stored for deploy.py compatibility; used in .desktop Comment.)
# -----------------------------------------------------------
TAB_COLOR="#787878"

# -----------------------------------------------------------
# Derived values (from this script's filesystem location)
# -----------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_NAME="$(basename "$REPO_DIR")"

# -----------------------------------------------------------
# Auto-install .desktop shortcuts on first run (idempotent)
# -----------------------------------------------------------
_install_desktop_entry() {
    local dest_dir="$1"
    local dest="$dest_dir/${REPO_NAME}-copilot.desktop"
    [ -f "$dest" ] && return
    mkdir -p "$dest_dir"
    cat > "$dest" << EOF
[Desktop Entry]
Type=Application
Name=$REPO_NAME (Copilot)
Comment=Open $REPO_NAME with GitHub Copilot CLI
Exec=lxterminal --working-directory="$REPO_DIR" --title="$REPO_NAME (Copilot)" -e "bash -c 'copilot --yolo --experimental; exec bash'"
Icon=utilities-terminal
Terminal=false
Categories=Development;
EOF
    chmod +x "$dest"
    echo "Installed .desktop shortcut: $dest"
}

_install_desktop_entry "$HOME/Desktop"
_install_desktop_entry "$HOME/.local/share/applications"

# -----------------------------------------------------------
# Launch LXTerminal with Copilot CLI
# -----------------------------------------------------------
lxterminal --working-directory="$REPO_DIR" --title="$REPO_NAME (Copilot)" -e "bash -c 'copilot --yolo --experimental; exec bash'" &
