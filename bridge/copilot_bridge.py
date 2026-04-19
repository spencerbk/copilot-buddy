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
import signal
import sys
import time

from bridge.transport_loopback import LoopbackTransport
from bridge.transport_serial import SerialTransport
from bridge.watcher import CopilotWatcher

log = logging.getLogger("copilot_bridge")

# Heartbeat cadence in seconds.
_HEARTBEAT_INTERVAL = 2.0


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
            _send_event(transport, evt)

        # --- Periodic heartbeat ------------------------------------
        now = time.monotonic()
        if now - last_heartbeat >= _HEARTBEAT_INTERVAL:
            # Include the active query/mode so the device can display it.
            active = next(iter(watcher.active_pids.values()), None)
            heartbeat = {
                "state": watcher.state,
                "query": active["query"] if active else "",
                "mode": active["mode"] if active else "suggest",
                "queries_today": watcher.queries_today,
                "total_queries": watcher.total_queries,
                "ts": int(time.time()),
            }
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

    # --- Watcher ---------------------------------------------------
    watcher = CopilotWatcher(poll_interval=args.poll_interval)

    # --- Graceful shutdown -----------------------------------------
    def _shutdown(signum: int, _frame: object) -> None:
        sig_name = signal.Signals(signum).name
        log.info("Received %s — shutting down", sig_name)
        transport.disconnect()
        log.info(
            "Session summary: %d queries today, %d total",
            watcher.queries_today,
            watcher.total_queries,
        )
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # --- Run -------------------------------------------------------
    log.info("Bridge running — monitoring Copilot CLI activity")
    try:
        run(transport, watcher)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()
