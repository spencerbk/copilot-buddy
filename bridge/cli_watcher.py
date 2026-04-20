"""File-based watcher for standalone Copilot CLI per-turn activity.

Watches ``~/.copilot/`` for two signals:

1. ``command-history-state.json`` mtime change → new user query (turn start)
2. ``session-state/*/events.jsonl`` quiescence → turn complete (turn end)

Works alongside the process-based :class:`~bridge.watcher.CopilotWatcher`.
The process watcher handles ``gh copilot suggest/explain`` (short-lived
processes); this module adds per-turn granularity for the long-lived
standalone ``copilot`` CLI.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import date
from pathlib import Path

log = logging.getLogger(__name__)

MAX_QUERY_LEN = 80
"""Maximum query string length forwarded to the device (RAM-friendly)."""

_DEFAULT_QUIESCENCE_SEC = 5.0
"""Seconds of silence on *all* ``events.jsonl`` files before we declare
a turn complete.  Needs to be long enough to span gaps between tool
calls (model-think time) but short enough for snappy pet reactions."""

_SESSION_STALENESS_SEC = 300.0
"""Ignore session directories whose ``events.jsonl`` hasn't been
touched in this many seconds — avoids scanning stale sessions."""


class CLIWatcher:
    """Detects per-turn activity in the standalone Copilot CLI.

    Parameters
    ----------
    copilot_dir:
        Path to the Copilot CLI data directory (default ``~/.copilot``).
    quiescence_sec:
        Seconds of ``events.jsonl`` silence before a turn is considered
        complete.
    """

    def __init__(
        self,
        copilot_dir: Path | str | None = None,
        quiescence_sec: float = _DEFAULT_QUIESCENCE_SEC,
    ) -> None:
        self.copilot_dir = Path(copilot_dir) if copilot_dir else Path.home() / ".copilot"
        self.quiescence_sec = quiescence_sec

        # Public state — mirrors CopilotWatcher's interface so the
        # bridge can read them the same way.
        self.state: str = "idle"
        self.query: str = ""
        self.queries_today: int = 0
        self.total_queries: int = 0

        # Internal paths
        self._history_path = self.copilot_dir / "command-history-state.json"
        self._session_dir = self.copilot_dir / "session-state"

        # File tracking
        self._history_mtime: float = 0.0

        # Session tracking: session_id → last known events.jsonl mtime
        self._session_mtimes: dict[str, float] = {}

        # Turn state machine
        self._turn_active: bool = False
        self._last_activity_mono: float = 0.0

        # Initialisation guard — first poll snapshots state without events
        self._initialized: bool = False

        self._today: str = date.today().isoformat()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def poll(self) -> list[dict]:
        """Check files for changes and return bridge-protocol events.

        Returns a list of event dicts:
        - ``{"evt": "start", "query": "...", "mode": "chat"}``
        - ``{"evt": "end", "preview": ""}``
        - ``{"evt": "milestone", "n": 50}``
        """
        if not self.copilot_dir.is_dir():
            return []

        self._maybe_reset_daily_count()
        now = time.monotonic()
        events: list[dict] = []

        # First poll: record current file state without emitting events.
        if not self._initialized:
            self._snapshot_initial_state()
            self._initialized = True
            return []

        # 1) Check command-history for a new user query.
        new_query = self._check_history()
        if new_query is not None:
            self._turn_active = True
            self._last_activity_mono = now
            self.query = new_query
            self.state = "busy"
            events.append({"evt": "start", "query": new_query, "mode": "chat"})
            log.info("CLI turn started: %s", new_query or "(empty query)")

        # 2) Check events.jsonl files for ongoing activity.
        if self._check_sessions():
            self._last_activity_mono = now

        # 3) Quiescence → turn complete.
        if self._turn_active and self._last_activity_mono > 0:
            silence = now - self._last_activity_mono
            if silence >= self.quiescence_sec:
                self._turn_active = False
                self.state = "idle"
                self.queries_today += 1
                self.total_queries += 1
                events.append({"evt": "end", "preview": ""})
                log.info("CLI turn ended (%.1fs quiescence)", silence)

                if self.queries_today > 0 and self.queries_today % 50 == 0:
                    events.append({"evt": "milestone", "n": self.queries_today})
                    log.info("Milestone: %d queries today", self.queries_today)

        return events

    # ------------------------------------------------------------------
    # Internals: initialisation
    # ------------------------------------------------------------------

    def _snapshot_initial_state(self) -> None:
        """Record initial file states without generating events."""
        try:
            if self._history_path.is_file():
                self._history_mtime = os.path.getmtime(self._history_path)
        except OSError:
            pass

        self._scan_sessions()

    # ------------------------------------------------------------------
    # Internals: command history
    # ------------------------------------------------------------------

    def _check_history(self) -> str | None:
        """Return the latest query if ``command-history-state.json`` changed.

        Returns ``None`` when no change is detected or on read error.
        """
        try:
            if not self._history_path.is_file():
                return None

            mtime = os.path.getmtime(self._history_path)
            if mtime <= self._history_mtime:
                return None

            # File changed — read the latest entry.
            self._history_mtime = mtime
            data = json.loads(self._history_path.read_text(encoding="utf-8"))
            history: list[str] = data.get("commandHistory", [])
            if not history:
                return None

            return str(history[0])[:MAX_QUERY_LEN]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            log.debug("Could not read command history: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Internals: session events
    # ------------------------------------------------------------------

    def _scan_sessions(self) -> None:
        """Discover active session directories and record their mtimes."""
        if not self._session_dir.is_dir():
            return

        now_epoch = time.time()
        try:
            for entry in self._session_dir.iterdir():
                if not entry.is_dir():
                    continue
                events_file = entry / "events.jsonl"
                if not events_file.is_file():
                    continue
                try:
                    mtime = os.path.getmtime(events_file)
                    if now_epoch - mtime < _SESSION_STALENESS_SEC:
                        self._session_mtimes[entry.name] = mtime
                except OSError:
                    continue
        except OSError:
            pass

    def _check_sessions(self) -> bool:
        """Check tracked sessions for new ``events.jsonl`` activity.

        Returns ``True`` if any session had new writes since last check.
        """
        if not self._session_dir.is_dir():
            return False

        any_activity = False
        now_epoch = time.time()

        try:
            for entry in self._session_dir.iterdir():
                if not entry.is_dir():
                    continue
                events_file = entry / "events.jsonl"
                if not events_file.is_file():
                    continue
                try:
                    mtime = os.path.getmtime(events_file)
                    if now_epoch - mtime > _SESSION_STALENESS_SEC:
                        self._session_mtimes.pop(entry.name, None)
                        continue
                    prev_mtime = self._session_mtimes.get(entry.name, 0.0)
                    if mtime > prev_mtime:
                        any_activity = True
                        self._session_mtimes[entry.name] = mtime
                except OSError:
                    continue
        except OSError:
            pass

        return any_activity

    # ------------------------------------------------------------------
    # Internals: daily reset
    # ------------------------------------------------------------------

    def _maybe_reset_daily_count(self) -> None:
        today = date.today().isoformat()
        if today != self._today:
            log.info(
                "CLI watcher midnight rollover — resetting queries_today (was %d)",
                self.queries_today,
            )
            self.queries_today = 0
            self._today = today
