"""Pet state machine for copilot-buddy.

Maps bridge events and heartbeats to one of seven pet states:
sleep, idle, busy, attention, celebrate, dizzy, heart.

Priority (highest first): dizzy > celebrate > heart > attention > busy > idle > sleep
"""

STATE_SLEEP = "sleep"
STATE_IDLE = "idle"
STATE_BUSY = "busy"
STATE_ATTENTION = "attention"
STATE_CELEBRATE = "celebrate"
STATE_DIZZY = "dizzy"
STATE_HEART = "heart"

# Hold durations for timed states (seconds)
HOLD_ATTENTION = 3.0
HOLD_CELEBRATE = 5.0
HOLD_DIZZY = 3.0
HOLD_HEART = 2.0

# Disconnect thresholds (seconds)
DISCONNECT_WARN = 10.0
DISCONNECT_SLEEP = 300.0

# Priority lookup — higher number wins
_PRIORITY = {
    STATE_SLEEP: 1,
    STATE_IDLE: 2,
    STATE_BUSY: 3,
    STATE_ATTENTION: 4,
    STATE_HEART: 5,
    STATE_CELEBRATE: 6,
    STATE_DIZZY: 7,
}

# Timed-state durations (only states that auto-expire)
_HOLD = {
    STATE_ATTENTION: HOLD_ATTENTION,
    STATE_CELEBRATE: HOLD_CELEBRATE,
    STATE_DIZZY: HOLD_DIZZY,
    STATE_HEART: HOLD_HEART,
}

# Heartbeat "state" string → base state
_HB_MAP = {
    "busy": STATE_BUSY,
    "idle": STATE_IDLE,
    "sleep": STATE_SLEEP,
    "error": STATE_DIZZY,
}


class StateManager:
    """Maps serial messages to the active pet state."""

    def __init__(self):
        self.state = STATE_SLEEP
        self.base_state = STATE_SLEEP
        self.query = ""
        self.mode = "suggest"
        self.queries_today = 0
        self.total_queries = 0
        self.disconnected = False

        self._timed_state = None
        self._timed_until = 0.0
        self._last_heartbeat = 0.0
        self._last_start_time = 0.0

    # ── public API ──────────────────────────────────────────────

    def process_message(self, msg, now):
        """Process a parsed message dict from serial_bridge.

        *msg* may be a heartbeat (has ``state`` key) or event
        (has ``evt`` key).  *now* is ``time.monotonic()``.
        Returns the new state string.
        """
        if not isinstance(msg, dict):
            return self.state

        if "evt" in msg:
            self._handle_event(msg, now)
        elif "state" in msg:
            self._handle_heartbeat(msg, now)

        return self._resolve(now)

    def update(self, now):
        """Tick — check timed-state expiry and disconnect.

        Returns the current state string.
        """
        return self._resolve(now)

    # ── event handling ──────────────────────────────────────────

    def _handle_event(self, msg, now):
        evt = msg["evt"]
        if evt == "start":
            self._last_start_time = now
            self.base_state = STATE_BUSY
        elif evt == "end":
            duration = now - self._last_start_time
            if duration < 3.0:
                self._set_timed(STATE_HEART, now)
            else:
                self._set_timed(STATE_ATTENTION, now)
            self.base_state = STATE_IDLE
        elif evt == "error":
            self._set_timed(STATE_DIZZY, now)
        elif evt == "milestone":
            self._set_timed(STATE_CELEBRATE, now)

    def _handle_heartbeat(self, msg, now):
        self._last_heartbeat = now
        self.disconnected = False
        self.query = msg.get("query", self.query)
        self.mode = msg.get("mode", self.mode)
        self.queries_today = msg.get("queries_today", self.queries_today)
        self.total_queries = msg.get("total_queries", self.total_queries)

        hb_state = msg.get("state", "idle")
        if hb_state == "error":
            self._set_timed(STATE_DIZZY, now)
        else:
            self.base_state = _HB_MAP.get(hb_state, STATE_IDLE)

    # ── timed-state logic ───────────────────────────────────────

    def _set_timed(self, new_state, now):
        """Set a timed state if it has higher priority than current."""
        duration = _HOLD.get(new_state, 3.0)
        if self._timed_state is not None:
            cur_pri = _PRIORITY.get(self._timed_state, 0)
            new_pri = _PRIORITY.get(new_state, 0)
            if new_pri < cur_pri and now < self._timed_until:
                return  # current timed state has higher priority
        self._timed_state = new_state
        self._timed_until = now + duration

    def _resolve(self, now):
        """Determine effective state from timed overlay + base + disconnect."""
        # Expire timed state
        if self._timed_state is not None and now >= self._timed_until:
            self._timed_state = None

        # Disconnect detection (only after first heartbeat)
        if self._last_heartbeat > 0:
            gap = now - self._last_heartbeat
            if gap >= DISCONNECT_SLEEP:
                self.base_state = STATE_SLEEP
                self.disconnected = True
            elif gap >= DISCONNECT_WARN:
                self.base_state = STATE_IDLE
                self.disconnected = True
            else:
                self.disconnected = False

        # Pick highest-priority active state
        if self._timed_state is not None:
            ts_pri = _PRIORITY.get(self._timed_state, 0)
            bs_pri = _PRIORITY.get(self.base_state, 0)
            self.state = self._timed_state if ts_pri >= bs_pri else self.base_state
        else:
            self.state = self.base_state

        return self.state
