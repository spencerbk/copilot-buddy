#!/usr/bin/env bash
# Copilot-buddy — hook wrapper for macOS / Linux (Bash)
# Invoked by Copilot CLI hooks. Passes the event name and stdin payload to
# the Python hook bridge. stdout MUST remain empty.
set -euo pipefail

EVENT_NAME="${1:?Usage: run-hook.sh <event_name>}"

# Resolve repo root relative to this script (.github/hooks/ -> repo root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BRIDGE_DIR="$REPO_ROOT/bridge"

# Set PYTHONPATH so hook_bridge is importable
export PYTHONPATH="${BRIDGE_DIR}${PYTHONPATH:+:$PYTHONPATH}"

# Find Python: prefer python3, fallback to python
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
fi

if [ -z "$PYTHON" ]; then
    # No Python found — fail silently, don't block Copilot
    exit 0
fi

# Forward stdin to Python, send stderr to stderr, keep stdout clean
exec "$PYTHON" -m hook_bridge "$EVENT_NAME" 2>&2

exit 0
