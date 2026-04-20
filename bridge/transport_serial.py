"""USB serial transport for copilot-buddy bridge.

Sends newline-delimited JSON to the ESP32 over a serial port.
Supports handshake-based auto-detection of the correct COM port.
"""

from __future__ import annotations

import json
import logging
import time

import serial
import serial.tools.list_ports

log = logging.getLogger(__name__)

# Minimum interval between reconnection attempts (seconds).
_RECONNECT_COOLDOWN = 5.0


class SerialTransport:
    """Manages a USB-serial link to the ESP32 companion device."""

    def __init__(
        self,
        port: str = "auto",
        baud: int = 115200,
        timeout: float = 5.0,
    ) -> None:
        self._port_spec: str = port
        self._baud: int = baud
        self._timeout: float = timeout

        self._serial: serial.Serial | None = None
        self._port: str | None = None
        self._last_reconnect_attempt: float = 0.0

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Open the serial connection.  Returns *True* on success."""
        port = self._port_spec
        if port == "auto":
            detected = self.auto_detect_port()
            if detected is None:
                log.warning("Auto-detect failed — no ESP32 device found")
                return False
            port = detected

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=self._baud,
                timeout=self._timeout,
                write_timeout=self._timeout,
            )
            self._port = port
            log.info("Connected to %s at %d baud", port, self._baud)
            return True
        except serial.SerialException as exc:
            log.error("Failed to open %s: %s", port, exc)
            self._serial = None
            return False

    def auto_detect_port(self) -> str | None:
        """Probe available COM ports for an ESP32 running copilot-buddy.

        Sends ``{"cmd":"status"}`` and looks for a JSON acknowledgement.
        """
        candidates = list(serial.tools.list_ports.comports())
        if not candidates:
            log.debug("No COM ports found on this system")
            return None

        log.debug(
            "Probing %d port(s): %s",
            len(candidates),
            ", ".join(p.device for p in candidates),
        )

        for port_info in candidates:
            device = port_info.device
            try:
                with serial.Serial(
                    port=device, baudrate=self._baud, timeout=2, write_timeout=2
                ) as probe:
                    # USB CDC needs a moment after port open before data flows
                    time.sleep(0.3)
                    # Drain any stale bytes sitting in the buffer
                    probe.reset_input_buffer()
                    probe.write(b'{"cmd":"status"}\n')
                    probe.flush()
                    raw = probe.readline()
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw.decode("utf-8", errors="replace"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    if data.get("ack") == "status":
                        log.info("Detected copilot-buddy on %s", device)
                        return device
            except serial.SerialException:
                log.debug("Could not open %s — skipping", device)
            except Exception:
                log.debug("Probe error on %s", device, exc_info=True)
        return None

    def disconnect(self) -> None:
        """Close the serial port cleanly."""
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
            self._port = None
            log.info("Serial connection closed")

    # ------------------------------------------------------------------
    # Data I/O
    # ------------------------------------------------------------------

    def send(self, data: str) -> bool:
        """Write *data* (should already include a trailing newline).

        Returns *True* on success.  On failure the transport is marked
        disconnected and a reconnection will be attempted on the next
        call.
        """
        if not self.connected:
            return self._try_reconnect_and_send(data)

        try:
            assert self._serial is not None
            self._serial.write(data.encode("utf-8"))
            self._serial.flush()
            return True
        except serial.SerialException as exc:
            log.warning("Serial write failed: %s", exc)
            self._mark_disconnected()
            return False

    def receive(self, timeout: float = 0.1) -> str | None:
        """Read one line from the device (with *timeout*).

        Returns the stripped line, or ``None`` if nothing was available.
        """
        if not self.connected or self._serial is None:
            return None
        prev_timeout = self._serial.timeout
        try:
            self._serial.timeout = timeout
            raw = self._serial.readline()
            if raw:
                return raw.decode("utf-8", errors="replace").strip()
            return None
        except serial.SerialException as exc:
            log.warning("Serial read failed: %s", exc)
            self._mark_disconnected()
            return None
        finally:
            if self._serial is not None:
                self._serial.timeout = prev_timeout

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        """``True`` when the serial port is open and presumed healthy."""
        return self._serial is not None and self._serial.is_open

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _mark_disconnected(self) -> None:
        try:
            if self._serial is not None:
                self._serial.close()
        except Exception:
            pass
        self._serial = None

    def _try_reconnect_and_send(self, data: str) -> bool:
        """Attempt to reconnect (rate-limited) then re-send."""
        now = time.monotonic()
        if now - self._last_reconnect_attempt < _RECONNECT_COOLDOWN:
            return False
        self._last_reconnect_attempt = now
        log.info("Attempting reconnection to %s …", self._port_spec)
        if self.connect():
            return self.send(data)
        return False
