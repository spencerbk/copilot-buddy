"""Fire-and-forget serial sender for copilot-buddy hook bridge.

Each invocation opens the port, writes one JSON line, and closes.
Never raises — hook scripts must not block Copilot CLI.
"""

from __future__ import annotations

import json
import logging
import time

log = logging.getLogger(__name__)

# Brief settle after opening USB CDC before writing
_POST_OPEN_SETTLE = 0.05


def send_message(
    port: str,
    baud: int,
    message: dict,
    *,
    timeout: float = 0.3,
) -> bool:
    """Serialize *message* as compact JSON and send to *port*.

    Returns ``True`` on success, ``False`` on any failure.
    """
    try:
        import serial  # noqa: PLC0415
    except ImportError:
        log.debug("pyserial not installed")
        return False

    data = (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")

    try:
        with serial.Serial(
            port=port,
            baudrate=baud,
            timeout=timeout,
            write_timeout=timeout,
        ) as ser:
            time.sleep(_POST_OPEN_SETTLE)
            ser.write(data)
            ser.flush()
        log.debug("Sent %d bytes to %s", len(data), port)
        return True
    except (OSError, serial.SerialException, serial.SerialTimeoutException) as exc:
        log.debug("Send failed on %s: %s", port, exc)
        return False


def log_message(message: dict) -> None:
    """Dry-run mode: log the message to stderr instead of sending."""
    import sys  # noqa: PLC0415

    line = json.dumps(message, separators=(",", ":"))
    print(f"[dry-run] {line}", file=sys.stderr)
