"""Serial port auto-detection for the copilot-buddy hook bridge.

Prefers the same status-handshake probe used by the daemon bridge, then falls
back to matching USB device descriptions when probing is unavailable.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

try:
    from bridge.transport_serial import SerialTransport
except ImportError:
    try:
        from transport_serial import SerialTransport  # type: ignore[no-redef]
    except ImportError:
        SerialTransport = None  # type: ignore[assignment,misc]


def detect_port(
    explicit_port: str | None,
    match_descriptions: list[str],
    baud: int = 115200,
) -> str | None:
    """Return the serial port to use, or ``None`` if unavailable.

     *explicit_port* is checked first (env var / config file override).
    Otherwise the daemon bridge's status-handshake probe runs first, then
    ``pyserial`` description matching is used as a fallback.
    """
    if explicit_port:
        return explicit_port

    if SerialTransport is not None:
        detected = SerialTransport(
            port="auto",
            baud=baud,
            timeout=0.3,
        ).auto_detect_port()
        if detected is not None:
            return detected

    try:
        import serial.tools.list_ports  # noqa: PLC0415
    except ImportError:
        log.debug("pyserial not installed — cannot match by description")
        return None

    try:
        ports = list(serial.tools.list_ports.comports())
    except OSError:
        log.debug("comports() failed", exc_info=True)
        return None

    if not ports:
        log.debug("No serial ports found")
        return None

    log.debug(
        "Found %d port(s): %s",
        len(ports),
        ", ".join(f"{p.device} ({p.description})" for p in ports),
    )

    for port_info in ports:
        desc = (port_info.description or "").lower()
        for pattern in match_descriptions:
            if pattern.lower() in desc:
                log.debug("Matched %s via pattern %r", port_info.device, pattern)
                return port_info.device

    log.debug("No matching port found")
    return None
