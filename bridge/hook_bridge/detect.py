"""Serial port auto-detection for the copilot-buddy hook bridge.

Detection priority:
1. Explicit port (env var / config file override)
2. Unique USB VID matching (instant, no port open required)
3. Status-handshake probe via SerialTransport (slower, opens each port)
4. USB description substring matching (broadest fallback)
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

# Known USB vendors used by supported ESP32-S2/S3 boards
_ADAFRUIT_VID = 0x239A
# Espressif VID (some ESP32-S2/S3 boards use native USB with this VID)
_ESPRESSIF_VID = 0x303A

_KNOWN_VIDS = frozenset({_ADAFRUIT_VID, _ESPRESSIF_VID})

try:
    from bridge.transport_serial import SerialTransport
except ImportError:
    try:
        from transport_serial import SerialTransport  # type: ignore[no-redef]
    except ImportError:
        SerialTransport = None  # type: ignore[assignment,misc]


def _detect_by_vid(known_vids: frozenset[int]) -> list[str]:
    """Return serial ports whose USB VID is in *known_vids*."""
    try:
        import serial.tools.list_ports  # noqa: PLC0415
    except ImportError:
        return []

    try:
        ports = list(serial.tools.list_ports.comports())
    except OSError:
        return []

    matches: list[str] = []
    for port_info in ports:
        if port_info.vid is not None and port_info.vid in known_vids:
            log.debug(
                "VID match: %s (vid=0x%04X, pid=0x%04X, desc=%s)",
                port_info.device,
                port_info.vid,
                port_info.pid or 0,
                port_info.description,
            )
            matches.append(port_info.device)

    return matches


def detect_port(
    explicit_port: str | None,
    match_descriptions: list[str],
    baud: int = 115200,
) -> str | None:
    """Return the serial port to use, or ``None`` if unavailable.

    *explicit_port* is checked first (env var / config file override).
    Then a unique USB VID match provides instant detection for Adafruit and
    Espressif boards. When multiple ports share the same VID (for example,
    dual-CDC boards exposing console + data ports), the daemon bridge's
    status-handshake probe runs next to disambiguate. Finally,
    ``pyserial`` description matching is used as a last resort.
    """
    if explicit_port:
        return explicit_port

    # Fast path: a single known VID match needs no probing.
    vid_matches = _detect_by_vid(_KNOWN_VIDS)
    if len(vid_matches) == 1:
        return vid_matches[0]
    if len(vid_matches) > 1:
        log.debug(
            "Multiple VID matches found (%s); probing to disambiguate",
            ", ".join(vid_matches),
        )

    # Handshake probe (slower — opens each port and sends a status command)
    if SerialTransport is not None:
        detected = SerialTransport(
            port="auto",
            baud=baud,
            timeout=0.3,
        ).auto_detect_port()
        if detected is not None:
            return detected

    # Broadest fallback: description substring matching
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
