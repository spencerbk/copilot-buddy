"""copilot-buddy bridge — monitors Copilot CLI and sends events to ESP32.

Usage:
    python copilot_bridge.py                        # auto-detect serial port
    python copilot_bridge.py --port COM3            # explicit port
    python copilot_bridge.py --transport loopback   # testing mode
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

from bridge.cli_watcher import CLIWatcher
from bridge.transport_loopback import LoopbackTransport
from bridge.transport_serial import SerialTransport
from bridge.watcher import CopilotWatcher

log = logging.getLogger("copilot_bridge")

# Heartbeat cadence in seconds.
_HEARTBEAT_INTERVAL = 2.0

# HUD transcript ring buffer config.
_MAX_ENTRIES = 5
_MAX_ENTRY_LEN = 20  # 20 chars visible at scale=2 on 240px display
_MAX_LINE_BYTES = 480  # leave headroom under 512-byte device limit


# ------------------------------------------------------------------
# Repo name detection
# ------------------------------------------------------------------

def _detect_repo_name() -> str:
    """Detect the current git repo name, falling back to CWD basename."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return os.path.basename(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return os.path.basename(os.getcwd())


_repo_name: str = ""


def _get_repo_name() -> str:
    """Return cached repo name (detected lazily on first call)."""
    global _repo_name  # noqa: PLW0603
    if not _repo_name:
        _repo_name = _detect_repo_name()
    return _repo_name


# ------------------------------------------------------------------
# Transcript ring buffer
# ------------------------------------------------------------------

_entries: list[str] = []


def _add_entry(query: str) -> None:
    """Prepend a repo-prefixed, timestamped query to the entries ring buffer."""
    repo = _get_repo_name()[:6]  # truncate repo name to 6 chars
    ts = datetime.now().strftime("%H:%M")
    # Format: "repo HH:MM query" — budget chars for repo + space + time + space
    prefix = f"{repo} {ts} "
    max_q = _MAX_ENTRY_LEN - len(prefix)
    q = query[:max_q] if query else "?"
    entry = f"{prefix}{q}"
    _entries.insert(0, entry)
    while len(_entries) > _MAX_ENTRIES:
        _entries.pop()


def _build_msg(state: str, connected: bool) -> str:
    """Build a one-line summary suitable for the HUD."""
    if not connected:
        return "No Copilot connected"
    if state == "busy":
        return "working..."
    if state == "sleep":
        return "sleeping"
    return "idle"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _build_transport(
    kind: str,
    port: str,
    baud: int,
) -> SerialTransport | LoopbackTransport:
    if kind == "loopback":
        return LoopbackTransport()
    return SerialTransport(port=port, baud=baud)


def _send_event(
    transport: SerialTransport | LoopbackTransport,
    payload: dict,
) -> None:
    """Serialise *payload* as newline-delimited JSON and send."""
    line = json.dumps(payload, separators=(",", ":")) + "\n"
    if not transport.send(line):
        log.warning("Failed to send: %s", line.rstrip())


# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------


def run(
    transport: SerialTransport | LoopbackTransport,
    watcher: CopilotWatcher,
    cli_watcher: CLIWatcher | None = None,
) -> None:
    """Core poll/send loop.  Runs until interrupted."""
    last_heartbeat = 0.0

    while True:
        # --- Poll for process changes ------------------------------
        try:
            events = watcher.poll()
        except Exception:
            log.error("Watcher poll failed", exc_info=True)
            events = []

        for evt in events:
            # Add start events to the transcript ring buffer
            if evt.get("evt") == "start" and evt.get("query"):
                _add_entry(evt["query"])
            _send_event(transport, evt)

        # --- Poll CLI file watcher ---------------------------------
        cli_events: list[dict] = []
        if cli_watcher is not None:
            try:
                cli_events = cli_watcher.poll()
            except Exception:
                log.error("CLI watcher poll failed", exc_info=True)

        for evt in cli_events:
            # Add start events to the transcript ring buffer
            if evt.get("evt") == "start" and evt.get("query"):
                _add_entry(evt["query"])
            _send_event(transport, evt)

        # --- Periodic heartbeat ------------------------------------
        now = time.monotonic()
        if now - last_heartbeat >= _HEARTBEAT_INTERVAL:
            # CLI watcher takes precedence when it has detected activity,
            # providing per-turn granularity for the standalone CLI.
            if cli_watcher is not None and (
                cli_watcher._turn_active or cli_watcher.total_queries > 0
            ):
                hb_state = cli_watcher.state
                hb_query = cli_watcher.query
                hb_mode = "chat"
                hb_queries_today = cli_watcher.queries_today + watcher.queries_today
                hb_total = cli_watcher.total_queries + watcher.total_queries
            else:
                active = next(iter(watcher.active_pids.values()), None)
                hb_state = watcher.state
                hb_query = active["query"] if active else ""
                hb_mode = active["mode"] if active else "suggest"
                hb_queries_today = watcher.queries_today
                hb_total = watcher.total_queries

            connected = hb_state != "sleep" or hb_total > 0

            heartbeat: dict = {
                "state": hb_state,
                "mode": hb_mode,
                "queries_today": hb_queries_today,
                "total_queries": hb_total,
                "ts": int(time.time()),
                "msg": _build_msg(hb_state, connected),
            }

            # Include entries if we have them (saves bytes vs always sending [])
            if _entries:
                heartbeat["entries"] = list(_entries)

            # Only include query when no entries (saves bytes)
            if not _entries and hb_query:
                heartbeat["query"] = hb_query

            # Safety: trim entries if serialized line exceeds byte budget
            line = json.dumps(heartbeat, separators=(",", ":"))
            while len(line.encode("utf-8")) > _MAX_LINE_BYTES and heartbeat.get("entries"):
                heartbeat["entries"].pop()
                if not heartbeat["entries"]:
                    del heartbeat["entries"]
                line = json.dumps(heartbeat, separators=(",", ":"))

            _send_event(transport, heartbeat)
            last_heartbeat = now

        time.sleep(watcher.poll_interval)


def main(argv: list[str] | None = None) -> None:
    """Entry point — parse args, connect, and enter the main loop."""
    parser = argparse.ArgumentParser(
        description="Bridge between GitHub Copilot CLI and the ESP32 desk pet.",
    )
    parser.add_argument(
        "--port",
        default="auto",
        help='Serial port (default: "auto" for auto-detection)',
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Serial baud rate (default: 115200)",
    )
    parser.add_argument(
        "--transport",
        choices=["serial", "loopback"],
        default="serial",
        help="Transport backend (default: serial)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Process scan interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--copilot-dir",
        default=None,
        help="Path to ~/.copilot directory (default: auto-detect)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args(argv)

    # --- Logging ---------------------------------------------------
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # --- Transport -------------------------------------------------
    transport = _build_transport(args.transport, args.port, args.baud)
    if not transport.connect():
        log.error("Could not connect transport — exiting")
        sys.exit(1)
    log.info("Transport ready (%s)", args.transport)

    # --- Watchers --------------------------------------------------
    watcher = CopilotWatcher(poll_interval=args.poll_interval)
    cli_watcher = CLIWatcher(copilot_dir=args.copilot_dir)
    log.info("CLI file watcher enabled (dir: %s)", cli_watcher.copilot_dir)

    # --- Graceful shutdown -----------------------------------------
    def _shutdown(signum: int, _frame: object) -> None:
        sig_name = signal.Signals(signum).name
        log.info("Received %s — shutting down", sig_name)
        transport.disconnect()
        total = watcher.queries_today + cli_watcher.queries_today
        log.info(
            "Session summary: %d queries today (%d process, %d CLI), %d total",
            total,
            watcher.queries_today,
            cli_watcher.queries_today,
            watcher.total_queries + cli_watcher.total_queries,
        )
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # --- Run -------------------------------------------------------
    log.info("Bridge running — monitoring Copilot CLI activity")
    try:
        run(transport, watcher, cli_watcher)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()
