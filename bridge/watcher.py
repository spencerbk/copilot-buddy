"""Monitor for GitHub Copilot CLI activity.

Scans the process table for Copilot CLI processes.  Supports both the
traditional ``gh copilot suggest/explain`` invocation and the standalone
``copilot`` CLI (e.g. ``copilot --yolo --experimental``).

Detection is best-effort — short-lived processes may be missed between
poll intervals.  The standalone CLI runs as a long-lived interactive
session, so the watcher provides **session-level** detection (busy while
running, idle when closed) rather than per-query granularity.
"""

from __future__ import annotations

import logging
import time
from datetime import date

import psutil

from bridge.constants import (
    EVT_END,
    EVT_MILESTONE,
    EVT_START,
    MAX_QUERY_LEN,
    MILESTONE_INTERVAL,
    STATE_BUSY,
    STATE_IDLE,
)

log = logging.getLogger(__name__)

# Flags that consume the next argument (e.g. ``-t shell``).
_FLAGS_WITH_VALUE = frozenset({"-t", "--target"})


def extract_query(cmdline: list[str]) -> str:
    """Pull the user's query text from a Copilot CLI command line.

    Looks for the first non-flag argument after ``suggest`` or ``explain``,
    skipping flags and their values (e.g. ``-t shell``).
    Returns an empty string when no query is found (including for the
    standalone ``copilot`` CLI which does not use subcommands).
    """
    for i, arg in enumerate(cmdline):
        low = arg.lower()
        if low in ("suggest", "explain"):
            # Walk remaining args, skipping flag+value pairs.
            skip_next = False
            for rest in cmdline[i + 1 :]:
                if skip_next:
                    skip_next = False
                    continue
                if rest in _FLAGS_WITH_VALUE:
                    skip_next = True
                    continue
                if rest.startswith("-"):
                    continue
                return rest[:MAX_QUERY_LEN]
            break
    return ""


def scan_processes() -> list[dict]:
    """Return currently-running Copilot CLI processes.

    Matches two invocation styles:
    - ``gh copilot suggest/explain`` — executable name is ``gh``
    - ``copilot [flags]`` — executable name is ``copilot``

    Each entry is ``{"pid": int, "mode": str, "query": str}``.
    Handles Windows quirks: *cmdline* can be ``None`` and system
    processes raise ``AccessDenied``.
    """
    results: list[dict] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline: list[str] | None = proc.info.get("cmdline")  # type: ignore[attr-defined]
            if not cmdline:
                continue

            name: str = (proc.info.get("name") or "").lower()  # type: ignore[attr-defined]
            basename = name.removesuffix(".exe")
            joined = " ".join(cmdline).lower()

            # Traditional: `gh copilot suggest/explain`
            is_gh_copilot = basename == "gh" and "copilot" in joined
            # Standalone: `copilot --yolo --experimental`
            is_standalone_copilot = basename == "copilot"

            if not is_gh_copilot and not is_standalone_copilot:
                continue

            mode = "explain" if "explain" in joined else "suggest"
            query = extract_query(cmdline)
            results.append({"pid": proc.info["pid"], "mode": mode, "query": query})  # type: ignore[index]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            # Defensive: never let one bad process kill the scan loop.
            log.debug("Unexpected error inspecting process", exc_info=True)
            continue
    return results


class CopilotWatcher:
    """Stateful monitor that detects new/ended Copilot CLI processes."""

    def __init__(self, poll_interval: float = 1.0) -> None:
        self.poll_interval: float = poll_interval

        self.active_pids: dict[int, dict] = {}  # pid -> process info
        self.state: str = STATE_IDLE

        self.queries_today: int = 0
        self.total_queries: int = 0

        self._today: str = date.today().isoformat()  # YYYY-MM-DD
        self._start_times: dict[int, float] = {}  # pid -> start timestamp

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def poll(self) -> list[dict]:
        """Scan processes, diff against known state, return events."""
        self._maybe_reset_daily_count()

        current = scan_processes()
        current_pids = {p["pid"] for p in current}
        current_map = {p["pid"]: p for p in current}

        events: list[dict] = []

        # --- Detect new processes ----------------------------------
        for pid, info in current_map.items():
            if pid not in self.active_pids:
                self._start_times[pid] = time.monotonic()
                events.append(
                    {"evt": EVT_START, "query": info["query"], "mode": info["mode"]}
                )
                log.info(
                    "Copilot %s started (pid %d): %s",
                    info["mode"],
                    pid,
                    info["query"] or "(no query captured)",
                )

        # --- Detect ended processes --------------------------------
        ended_pids = set(self.active_pids) - current_pids
        for pid in ended_pids:
            duration = time.monotonic() - self._start_times.pop(pid, time.monotonic())
            events.append({"evt": EVT_END, "preview": ""})

            self.queries_today += 1
            self.total_queries += 1
            log.info("Copilot query ended (pid %d, %.1fs)", pid, duration)

            # Fast response → "heart" animation on device.
            if duration < 3.0:
                log.debug("Fast query (<3s) — heart state eligible")

            # Milestone every 50 queries.
            if self.queries_today > 0 and self.queries_today % MILESTONE_INTERVAL == 0:
                events.append({"evt": EVT_MILESTONE, "n": self.queries_today})
                log.info("Milestone reached: %d queries today", self.queries_today)

        # --- Update bookkeeping ------------------------------------
        self.active_pids = current_map
        self.state = STATE_BUSY if current_pids else STATE_IDLE
        return events

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _maybe_reset_daily_count(self) -> None:
        today = date.today().isoformat()
        if today != self._today:
            log.info(
                "Midnight rollover — resetting queries_today (was %d)",
                self.queries_today,
            )
            self.queries_today = 0
            self._today = today
