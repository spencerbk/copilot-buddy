"""Device-side serial bridge for copilot-buddy.

Reads newline-delimited JSON from the host bridge via usb_cdc.data.
Non-blocking — call read_message() in the main loop.
"""

import gc
import json
import time


class SerialBridge:
    """Non-blocking JSON reader/writer for the USB CDC data port."""

    def __init__(self, serial_port, device_info=None):
        """Wrap *serial_port* (usb_cdc.data, may be None).

        *device_info* is an optional dict with static device metadata
        (e.g. ``{"pet": "octocat", "display": "ST7789"}``) included
        in status responses.
        """
        self._serial = serial_port
        self._buf = bytearray()
        self._max_line = 512
        self._start_time = time.monotonic()
        self._device_info = device_info or {}

    # ── public API ──────────────────────────────────────────────

    def read_message(self):
        """Non-blocking read.  Returns a parsed dict or None.

        Reads available bytes into an internal buffer.  When a newline
        is found the line is decoded, parsed as JSON, and returned.
        Any bytes after the newline stay in the buffer for the next call.
        Malformed lines are printed as warnings and skipped.
        """
        if self._serial is None:
            return None

        avail = self._serial.in_waiting
        if avail > 0:
            chunk = self._serial.read(avail)
            if chunk:
                self._buf.extend(chunk)

        nl = self._buf.find(b"\n")
        if nl < 0:
            # No complete line yet; guard against runaway buffer
            if len(self._buf) > self._max_line:
                self._buf = bytearray()
            return None

        # Extract line up to newline, keep remainder in _buf
        line_bytes = bytes(self._buf[:nl])
        self._buf = self._buf[nl + 1:]

        return self._process_line(line_bytes)

    def send_response(self, data):
        """Send a JSON dict back to the host bridge."""
        if self._serial is None:
            return
        try:
            payload = json.dumps(data) + "\n"
            self._serial.write(payload.encode("utf-8"))
        except OSError as exc:
            print("serial_bridge: write error:", exc)

    # ── internals ───────────────────────────────────────────────

    def _process_line(self, line_bytes):
        """Decode the buffered line, parse JSON, handle built-in cmds."""
        line = line_bytes.decode("utf-8").strip()

        if not line:
            return None

        try:
            msg = json.loads(line)
        except ValueError:
            print("serial_bridge: bad JSON:", line[:80])
            return None

        # Built-in: respond to status queries from the host
        if isinstance(msg, dict) and msg.get("cmd") == "status":
            self._handle_status()
            return None

        return msg

    def _handle_status(self):
        """Respond with device info for host-side diagnostics."""
        gc.collect()
        data = {
            "uptime": int(time.monotonic() - self._start_time),
            "heap_free": gc.mem_free(),
        }
        data.update(self._device_info)
        self.send_response({"ack": "status", "ok": True, "data": data})
