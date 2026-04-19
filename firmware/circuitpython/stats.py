"""Persistent stats tracking for copilot-buddy.

Tracks query counts and uptime. Persists to /stats.json with
atomic writes (temp file + rename) to prevent corruption.
Uses the bridge's timestamp as authoritative clock.
"""

import json
import os
import time


class Stats:
    """Persistent query and uptime statistics."""

    _STATS_PATH = "/stats.json"
    _TMP_PATH = "/stats_tmp.json"
    _SAVE_DEBOUNCE = 60  # seconds between auto-saves

    def __init__(self):
        self.queries_today = 0
        self.total_queries = 0
        self.last_date = ""
        self._last_save = 0.0
        self._dirty = False
        self._load()

    def record_query(self, bridge_ts=None):
        """Increment query count; reset daily count if date changed.

        Args:
            bridge_ts: Unix timestamp from the host bridge. If None
                       (no heartbeat yet), only total_queries is bumped.
        """
        self.total_queries += 1
        self._dirty = True

        if bridge_ts is not None:
            today = _ts_to_date(bridge_ts)
            if today != self.last_date:
                self.queries_today = 0
                self.last_date = today
        self.queries_today += 1

    def save(self):
        """Save stats if dirty and debounce interval has elapsed."""
        if not self._dirty:
            return
        now = time.monotonic()
        if now - self._last_save < self._SAVE_DEBOUNCE:
            return
        self._write()

    def force_save(self):
        """Save immediately, ignoring debounce (use on shutdown)."""
        if self._dirty:
            self._write()

    # ── internals ───────────────────────────────────────────────

    def _load(self):
        """Read stats from disk; fall back to temp file, then zeros."""
        try:
            with open(self._STATS_PATH, "r") as f:
                data = json.load(f)
            self.queries_today = data.get("queries_today", 0)
            self.total_queries = data.get("total_queries", 0)
            self.last_date = data.get("last_date", "")
            return
        except (OSError, ValueError, KeyError):
            pass

        # Recover from temp file left by interrupted atomic write
        try:
            with open(self._TMP_PATH, "r") as f:
                data = json.load(f)
            self.queries_today = data.get("queries_today", 0)
            self.total_queries = data.get("total_queries", 0)
            self.last_date = data.get("last_date", "")
            os.rename(self._TMP_PATH, self._STATS_PATH)
        except (OSError, ValueError, KeyError):
            pass

    def _write(self):
        """Atomic write: temp file then rename."""
        data = {
            "queries_today": self.queries_today,
            "total_queries": self.total_queries,
            "last_date": self.last_date,
        }
        try:
            with open(self._TMP_PATH, "w") as f:
                json.dump(data, f)
            os.rename(self._TMP_PATH, self._STATS_PATH)
            self._last_save = time.monotonic()
            self._dirty = False
        except OSError as exc:
            print("stats: save failed:", exc)


def _ts_to_date(ts):
    """Convert a unix timestamp to 'YYYY-MM-DD' using time.localtime."""
    t = time.localtime(int(ts))
    return "{:04d}-{:02d}-{:02d}".format(t.tm_year, t.tm_mon, t.tm_mday)
