"""Map Copilot CLI hook events to copilot-buddy's existing JSON protocol.

Each function returns a list of message dicts to send to the device.
Messages use the same format the firmware already understands: heartbeat
messages (with ``state`` key) and event messages (with ``evt`` key).
"""

from __future__ import annotations

import time
from typing import Any

from bridge.constants import (
    EVT_END,
    EVT_ERROR,
    EVT_START,
    MAX_QUERY_LEN,
    STATE_BUSY,
    STATE_IDLE,
    STATE_SLEEP,
)

from .stats import HookStats

# Events that produce no serial message
_SILENT_EVENTS = frozenset({"preCompact", "notification"})


def _ts() -> int:
    """Current Unix epoch seconds."""
    return int(time.time())


def _heartbeat(
    state: str,
    stats: HookStats,
    msg: str,
) -> dict[str, Any]:
    """Build a heartbeat-style message (resets firmware disconnect timer)."""
    hb: dict[str, Any] = {
        "state": state,
        "ts": _ts(),
        "queries_today": stats.queries_today,
        "total_queries": stats.total_queries,
        "msg": msg,
    }
    if stats.entries:
        hb["entries"] = stats.entries
    return hb


def build_messages(
    event_name: str,
    payload: dict[str, Any],
    stats: HookStats,
) -> list[dict[str, Any]]:
    """Translate a Copilot CLI hook event into copilot-buddy protocol messages.

    Returns a list of message dicts (usually one, sometimes two when a
    milestone fires alongside an event).
    """
    if event_name in _SILENT_EVENTS:
        return []

    messages: list[dict[str, Any]] = []

    if event_name == "sessionStart":
        messages.append(_heartbeat(STATE_IDLE, stats, "connected"))

    elif event_name == "sessionEnd":
        messages.append(_heartbeat(STATE_SLEEP, stats, "session ended"))

    elif event_name == "userPromptSubmitted":
        # Extract query from the hook payload
        query = ""
        user_msg = payload.get("userMessage")
        if isinstance(user_msg, dict):
            query = str(user_msg.get("content", ""))[:MAX_QUERY_LEN]
        elif isinstance(user_msg, str):
            query = user_msg[:MAX_QUERY_LEN]
        messages.append({"evt": EVT_START, "query": query, "mode": "chat"})

    elif event_name == "preToolUse":
        tool = str(payload.get("toolName", "tool"))
        messages.append(_heartbeat(STATE_BUSY, stats, f"{tool}..."))

    elif event_name == "postToolUse":
        tool = str(payload.get("toolName", "tool"))
        messages.append(_heartbeat(STATE_BUSY, stats, f"{tool} ok"))

    elif event_name == "postToolUseFailure":
        tool = str(payload.get("toolName", "tool"))
        messages.append({"evt": EVT_ERROR, "msg": f"{tool} failed"})

    elif event_name == "permissionRequest":
        messages.append(_heartbeat(STATE_BUSY, stats, "awaiting permission"))

    elif event_name == "subagentStart":
        agent = str(payload.get("agentName", "subagent"))
        messages.append(_heartbeat(STATE_BUSY, stats, f"{agent}..."))

    elif event_name == "subagentStop":
        messages.append(_heartbeat(STATE_BUSY, stats, "working..."))

    elif event_name == "agentStop":
        messages.append({"evt": EVT_END, "preview": ""})

    elif event_name == "errorOccurred":
        error_obj = payload.get("error")
        msg = "error"
        if isinstance(error_obj, dict):
            msg = str(error_obj.get("message", error_obj.get("name", "error")))[:60]
        messages.append({"evt": EVT_ERROR, "msg": msg})

    else:
        # Unknown event — send a heartbeat to keep the connection alive
        messages.append(_heartbeat(STATE_IDLE, stats, "idle"))

    return messages
