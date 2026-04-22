"""CLI entry point for copilot-buddy hook invocations.

Invoked as ``python -m hook_bridge <event_name>``.
The Copilot CLI passes the hook payload as JSON on **stdin**.

**stdout must remain empty** — Copilot interprets stdout as control JSON
for ``preToolUse`` / ``permissionRequest`` hooks.
"""

from __future__ import annotations

import json
import logging
import sys

from .config import load_config
from .detect import detect_port
from .events import build_messages
from .locking import hook_lock
from .sender import log_message, send_message
from .stats import load_stats, record_query, refresh_day, save_stats

from bridge.constants import EVT_MILESTONE, MAX_QUERY_LEN

# All logging goes to stderr — stdout is reserved for Copilot control JSON
logging.basicConfig(
    stream=sys.stderr,
    level=logging.WARNING,
    format="[copilot-buddy] %(levelname)s: %(message)s",
)

_LOG_LEVEL_VAR = "COPILOT_BUDDY_LOG_LEVEL"


def main() -> None:
    """Read an event from argv/stdin, normalize it, and send to the device."""
    log = logging.getLogger("hook_bridge")

    # Allow debug logging via env var
    import os  # noqa: PLC0415

    level = os.environ.get(_LOG_LEVEL_VAR, "").upper()
    if level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        logging.getLogger().setLevel(level)

    try:
        if len(sys.argv) < 2:
            log.error("Usage: python -m hook_bridge <event_name>")
            sys.exit(1)

        event_name: str = sys.argv[1]

        # Read payload from stdin
        raw = sys.stdin.read()
        try:
            payload: dict = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, ValueError):
            payload = {}

        # Load config
        config = load_config()

        with hook_lock(timeout=config.serial_timeout) as acquired:
            if not acquired:
                log.debug("Hook lock busy — skipping event %s", event_name)
                sys.exit(0)

            stats = load_stats()
            stats_changed = refresh_day(stats)

            # Track query on prompt submission
            if event_name == "userPromptSubmitted":
                query = ""
                user_msg = payload.get("userMessage")
                if isinstance(user_msg, dict):
                    query = str(user_msg.get("content", ""))[:MAX_QUERY_LEN]
                elif isinstance(user_msg, str):
                    query = user_msg[:MAX_QUERY_LEN]
                record_query(stats, query)
                stats_changed = True

            if stats_changed:
                save_stats(stats)

            # Build protocol messages
            messages = build_messages(event_name, payload, stats)
            if not messages:
                log.debug("No messages for event %s", event_name)
                sys.exit(0)

            # Send milestone event if one was triggered
            if stats.milestone is not None:
                messages.append({"evt": EVT_MILESTONE, "n": stats.milestone})

            # Send to device
            if config.dry_run:
                for msg in messages:
                    log_message(msg)
            else:
                port = detect_port(
                    config.serial_port,
                    config.device_match_descriptions,
                    baud=config.baud,
                )
                if port is None:
                    log.debug("No serial port found — skipping")
                    sys.exit(0)
                for msg in messages:
                    send_message(
                        port,
                        config.baud,
                        msg,
                        timeout=config.serial_timeout,
                    )

    except SystemExit:
        raise
    except Exception:
        log.error("Unexpected error in hook_bridge", exc_info=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
