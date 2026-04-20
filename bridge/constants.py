"""Shared constants for all copilot-buddy bridge modes.

Both the daemon bridge (copilot_bridge / watcher / cli_watcher) and the
hook bridge import from here so behavioral contracts stay in sync.
"""

# --- Query / HUD display limits ------------------------------------------

MAX_QUERY_LEN: int = 80
"""Maximum query string length forwarded to the device (RAM-friendly)."""

MAX_ENTRIES: int = 5
"""Maximum number of HUD transcript entries shown on the device."""

MAX_ENTRY_LEN: int = 20
"""Max characters per HUD entry (20 chars visible at scale=2 on 240px display)."""

# --- Milestone ------------------------------------------------------------

MILESTONE_INTERVAL: int = 50
"""Fire a milestone event every N queries *today* (daily, not all-time)."""

# --- Device states --------------------------------------------------------

STATE_IDLE: str = "idle"
STATE_BUSY: str = "busy"
STATE_SLEEP: str = "sleep"

# --- Protocol event keys --------------------------------------------------

EVT_START: str = "start"
EVT_END: str = "end"
EVT_ERROR: str = "error"
EVT_MILESTONE: str = "milestone"
