#!/bin/bash
# ============================================================
# open-copilot.command
#
# Double-click in Finder to open an iTerm2 window for this repo
# with GitHub Copilot CLI running.
#
# On first run, also installs an iTerm2 Dynamic Profile so the
# profile appears in the Profiles menu (detected automatically).
#
# To use in another repo: copy this file to <repo>/scripts/
# and change only TAB_COLOR below.
# ============================================================

# -----------------------------------------------------------
# User-configurable: tab color (hex). Change per repo.
# -----------------------------------------------------------
TAB_COLOR="#787878"

# -----------------------------------------------------------
# Derived values (from this script's filesystem location)
# -----------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_NAME="$(basename "$REPO_DIR")"

# -----------------------------------------------------------
# Hex-to-iTerm2 color conversion (0.0–1.0 components)
# -----------------------------------------------------------
hex_to_float() {
    printf "%.6f" "$(echo "scale=6; $((16#$1)) / 255" | bc)"
}

R=$(hex_to_float "${TAB_COLOR:1:2}")
G=$(hex_to_float "${TAB_COLOR:3:2}")
B=$(hex_to_float "${TAB_COLOR:5:2}")

# -----------------------------------------------------------
# Deterministic GUID from repo name (stable across runs)
# -----------------------------------------------------------
HASH=$(echo -n "${REPO_NAME}-copilot" | md5 | head -c 32)
GUID="${HASH:0:8}-${HASH:8:4}-${HASH:12:4}-${HASH:16:4}-${HASH:20:12}"

# -----------------------------------------------------------
# Auto-install iTerm2 Dynamic Profile on first run (idempotent)
# -----------------------------------------------------------
PROFILE_DIR="$HOME/Library/Application Support/iTerm2/DynamicProfiles"
PROFILE_PATH="$PROFILE_DIR/${REPO_NAME}-copilot.json"

if [ ! -f "$PROFILE_PATH" ]; then
    mkdir -p "$PROFILE_DIR"
    cat > "$PROFILE_PATH" << EOF
{
  "Profiles": [
    {
      "Name": "$REPO_NAME (Copilot)",
      "Guid": "$GUID",
      "Working Directory": "$REPO_DIR",
      "Custom Directory": "Yes",
      "Initial Text": "copilot --yolo --experimental",
      "Tab Color": {
        "Red Component": $R,
        "Green Component": $G,
        "Blue Component": $B,
        "Color Space": "sRGB",
        "Alpha Component": 1.0
      },
      "Use Tab Color": true,
      "Tags": ["repos"]
    }
  ]
}
EOF
    echo "Installed iTerm2 Dynamic Profile: $PROFILE_PATH"
    echo "The profile will appear in iTerm2's Profiles menu automatically."
    sleep 1
fi

# -----------------------------------------------------------
# Launch iTerm2 window with the profile.
# Uses try/on error so first run works even if iTerm2 hasn't
# detected the new Dynamic Profile yet — mirrors the Windows
# script's inline-args approach for immediate launch.
# -----------------------------------------------------------
osascript << APPLESCRIPT
tell application "iTerm"
    launch
    try
        create window with profile "$REPO_NAME (Copilot)"
    on error
        -- Profile not loaded yet; fall back to direct session
        create window with default profile
        tell current session of current window
            write text "cd '$REPO_DIR' && copilot --yolo --experimental"
        end tell
    end try
    activate
end tell
APPLESCRIPT
