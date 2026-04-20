"""Persistent stats for copilot-buddy hook bridge.

Each hook invocation is a separate process, so query counters and HUD
entries are persisted in ``~/.copilot-buddy/hook-state.json``.

Writes are atomic (temp file + ``os.replace``) to avoid corruption when
concurrent hooks fire simultaneously.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime

from bridge.constants import MAX_ENTRIES, MAX_ENTRY_LEN, MILESTONE_INTERVAL

log = logging.getLogger(__name__)

_STATE_DIR = os.path.join(os.path.expanduser("~"), ".copilot-buddy")
_STATE_FILE = os.path.join(_STATE_DIR, "hook-state.json")


@dataclass
class HookStats:
    """In-memory snapshot of persisted hook state."""

    queries_today: int = 0
    total_queries: int = 0
    last_date: str = ""
    entries: list[str] = field(default_factory=list)

    # Set after record_query when a milestone is hit
    milestone: int | None = None


def _repo_prefix() -> str:
    """Return a short repo name from the cwd (max 6 chars)."""
    name = os.path.basename(os.getcwd()) or "repo"
    return name[:6]


def load_stats() -> HookStats:
    """Read stats from disk.  Returns defaults on any failure."""
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return HookStats()
        return HookStats(
            queries_today=int(data.get("queries_today", 0)),
            total_queries=int(data.get("total_queries", 0)),
            last_date=str(data.get("last_date", "")),
            entries=list(data.get("entries", [])),
        )
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return HookStats()


def refresh_day(stats: HookStats) -> bool:
    """Reset daily counters when the local calendar day changes."""
    today = date.today().isoformat()
    if stats.last_date == today:
        return False
    stats.queries_today = 0
    stats.last_date = today
    stats.milestone = None
    return True


def save_stats(stats: HookStats) -> None:
    """Write stats atomically to disk."""
    os.makedirs(_STATE_DIR, exist_ok=True)
    data = {
        "queries_today": stats.queries_today,
        "total_queries": stats.total_queries,
        "last_date": stats.last_date,
        "entries": stats.entries[:MAX_ENTRIES],
    }
    try:
        fd, tmp = tempfile.mkstemp(
            dir=_STATE_DIR, suffix=".tmp", prefix="hook-state-"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(tmp, _STATE_FILE)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError as exc:
        log.debug("Stats save failed: %s", exc)


def record_query(stats: HookStats, query: str) -> None:
    """Increment counters and add a HUD entry for a new query.

    Sets ``stats.milestone`` when today's query count hits a multiple of 50.
    """
    refresh_day(stats)

    stats.queries_today += 1
    stats.total_queries += 1

    # HUD entry: "repo  HH:MM query"
    repo = _repo_prefix()
    ts = datetime.now().strftime("%H:%M")
    prefix = f"{repo} {ts} "
    max_q = MAX_ENTRY_LEN - len(prefix)
    q = (query[:max_q] if query else "?").strip()
    entry = f"{prefix}{q}"
    stats.entries.insert(0, entry)
    while len(stats.entries) > MAX_ENTRIES:
        stats.entries.pop()

    # Milestone check
    if stats.queries_today > 0 and stats.queries_today % MILESTONE_INTERVAL == 0:
        stats.milestone = stats.queries_today
    else:
        stats.milestone = None
