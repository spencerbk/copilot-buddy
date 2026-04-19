"""Device-side serial bridge for copilot-buddy (MicroPython).

Reads newline-delimited JSON from the host bridge via USB serial.
Non-blocking — call read_message() in the main loop.

On ESP32-S3, USB CDC serial is accessed via sys.stdin/sys.stdout
with select.poll() for non-blocking checks.
"""

import gc
import sys
import time

try:
    import ujson as json
except ImportError:
    import json

try:
    import select
    _poll = select.poll()
    _poll.register(sys.stdin, select.POLLIN)
    _HAS_POLL = True
except (ImportError, OSError):
    _HAS_POLL = False


class SerialBridge:
    """Non-blocking JSON reader/writer for USB serial."""

    def __init__(self, device_info=None):
        """Create a serial bridge.

        *device_info* is an optional dict with static device metadata
        (e.g. ``{"pet": "octocat", "display": "ST7789"}``) included
        in status responses.
        """
        self._buf = bytearray()
        self._max_line = 512
        self._start_ticks = time.ticks_ms()
        self._device_info = device_info or {}

    # ── public API ──────────────────────────────────────────────

    def read_message(self):
        """Non-blocking read.  Returns a parsed dict or None.

        Reads available bytes into an internal buffer.  When a newline
        is found the line is decoded, parsed as JSON, and returned.
        Malformed lines are printed as warnings and skipped.
        """
        while self._has_data():
            try:
                chunk = sys.stdin.read(1)
            except OSError:
                break
            if not chunk:
                break
            byte_val = ord(chunk)
            if byte_val == ord("\n"):
                result = self._process_line()
                if result is not None:
                    return result
            elif len(self._buf) < self._max_line:
                self._buf.append(byte_val)
        return None

    def send_response(self, data):
        """Send a JSON dict back to the host bridge."""
        try:
            payload = json.dumps(data) + "\n"
            sys.stdout.write(payload)
        except OSError as exc:
            print("serial_bridge: write error:", exc)

    # ── internals ───────────────────────────────────────────────

    def _has_data(self):
        """Check if stdin has data without blocking."""
        if _HAS_POLL:
            return bool(_poll.poll(0))
        return False

    def _process_line(self):
        """Decode the buffered line, parse JSON, handle built-in cmds."""
        try:
            line = bytes(self._buf).decode("utf-8").strip()
        except UnicodeError:
            del self._buf[:]
            return None
        del self._buf[:]

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
        uptime_ms = time.ticks_diff(time.ticks_ms(), self._start_ticks)
        data = {
            "uptime": uptime_ms // 1000,
            "heap_free": gc.mem_free(),
        }
        data.update(self._device_info)
        self.send_response({"ack": "status", "ok": True, "data": data})
