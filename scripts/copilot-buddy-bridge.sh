#!/usr/bin/env bash
# ============================================================
# copilot-buddy-bridge.sh
#
# Stable launcher for the copilot-buddy bridge daemon.
# Resolves the .venv Python at runtime so the service definition
# does not break when the venv is recreated.
#
# Usage (typically invoked by launchd/systemd, not manually):
#   copilot-buddy-bridge.sh [--port /dev/ttyACM0] [--log-file ...] ...
# ============================================================

set -euo pipefail

# Derive repo root from this script's location (scripts/ → repo root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve Python from the repo-root .venv
VENV_PYTHON="$REPO_DIR/.venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $REPO_DIR/.venv" >&2
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && python -m pip install -r bridge/requirements.txt" >&2
    exit 1
fi

# Run the bridge daemon from the repo root, passing through all args
cd "$REPO_DIR"
exec "$VENV_PYTHON" -m bridge.copilot_bridge "$@"
