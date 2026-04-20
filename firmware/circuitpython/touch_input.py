"""Capacitive touch input for copilot-buddy.

Drives the FT6206/FT6236 touch controller found on the Adafruit 2.8" TFT
ILI9341 capacitive-touch breakout.  Connected via STEMMA QT I2C on the
QT Py ESP32-S2.

Provides the same event interface as ``Button``:
    ``update(now)`` → ``"short_press"`` / ``"long_press"`` / ``None``

Gesture mapping:
    Tap   (touch + release, <0.5 s, <15 px drift)  → ``"short_press"``
    Swipe (horizontal movement > 50 px)             → ``"long_press"``

Requires ``adafruit_focaltouch`` and ``adafruit_bus_device`` from the
Adafruit CircuitPython Bundle.
"""

import busio

# Thresholds
_TAP_MAX_DURATION = 0.5   # seconds
_TAP_MAX_DRIFT = 15       # pixels (logical)
_SWIPE_MIN_DISTANCE = 50  # pixels (logical, horizontal)
_SWIPE_DIR_MARGIN = 10    # swipe must dominate the other axis by this much


class TouchInput:
    """Capacitive touch gesture detector (FT6206/FT6236).

    Matches the ``Button`` interface — call ``update(now)`` each tick.
    Falls back to a no-op if the touch controller is absent or init fails.
    """

    def __init__(self, config):
        self._enabled = False
        self._i2c = None

        touch_addr = config.get("touch_i2c_addr")
        if touch_addr is None:
            return  # no touch configured for this board

        sda_pin = config.get("touch_sda")
        scl_pin = config.get("touch_scl")
        if sda_pin is None or scl_pin is None:
            return

        try:
            import adafruit_focaltouch  # noqa: PLC0415

            # Prefer board.STEMMA_I2C() — the Adafruit-recommended singleton
            # for STEMMA QT I2C devices.  Falls back to raw busio.I2C() for
            # non-Adafruit boards or when STEMMA_I2C is unavailable.
            i2c = None
            try:
                import board as _board  # noqa: PLC0415
                i2c = _board.STEMMA_I2C()
            except (ImportError, AttributeError, RuntimeError, ValueError):
                pass
            if i2c is None:
                i2c = busio.I2C(scl_pin, sda_pin)

            self._ft = adafruit_focaltouch.Adafruit_FocalTouch(
                i2c, address=touch_addr,
            )
            self._i2c = i2c
            self._enabled = True
            print("Touch: FT6206 on I2C addr 0x{:02X}".format(touch_addr))
        except Exception as exc:
            print("WARN: touch init failed: {}".format(exc))
            return

        # Display rotation for coordinate mapping
        self._rotation = config.get("rotation", 0)
        self._native_w = config.get("width", 240)
        self._native_h = config.get("height", 320)

        # Gesture state machine
        self._touching = False
        self._start_x = 0
        self._start_y = 0
        self._last_x = 0
        self._last_y = 0
        self._start_time = 0.0
        self._swipe_fired = False  # suppress tap after swipe

    def update(self, now):
        """Poll touch and return an event string or None.

        Returns:
            "short_press" — tap (touch + release, <0.5 s, <15 px drift).
            "long_press"  — horizontal swipe (>50 px).
            None          — no event this tick.
        """
        if not self._enabled:
            return None

        try:
            touches = self._ft.touches
        except OSError:
            return None

        if touches:
            raw_x = touches[0]["x"]
            raw_y = touches[0]["y"]
            lx, ly = self._map_coords(raw_x, raw_y)

            if not self._touching:
                # Touch start
                self._touching = True
                self._start_x = lx
                self._start_y = ly
                self._last_x = lx
                self._last_y = ly
                self._start_time = now
                self._swipe_fired = False
                return None

            # Track last position for drift calculation
            self._last_x = lx
            self._last_y = ly

            # Still touching — check for swipe
            if not self._swipe_fired:
                dx = lx - self._start_x
                dy = ly - self._start_y
                if (abs(dx) >= _SWIPE_MIN_DISTANCE
                        and abs(dx) > abs(dy) + _SWIPE_DIR_MARGIN):
                    self._swipe_fired = True
                    return "long_press"

            return None

        # No touches — was touching before?
        if self._touching:
            self._touching = False

            # If swipe already fired, suppress tap
            if self._swipe_fired:
                return None

            # Check for tap (short duration + minimal drift)
            held = now - self._start_time
            dx = abs(self._last_x - self._start_x)
            dy = abs(self._last_y - self._start_y)
            drift = max(dx, dy)
            if held <= _TAP_MAX_DURATION and drift <= _TAP_MAX_DRIFT:
                return "short_press"

        return None

    def _map_coords(self, raw_x, raw_y):
        """Map raw FT6206 coordinates to logical display coordinates."""
        w = self._native_w
        h = self._native_h
        r = self._rotation

        if r == 0:
            return raw_x, raw_y
        if r == 90:
            return raw_y, (w - 1 - raw_x)
        if r == 180:
            return (w - 1 - raw_x), (h - 1 - raw_y)
        if r == 270:
            return (h - 1 - raw_y), raw_x
        return raw_x, raw_y

    @property
    def is_pressed(self):
        """Return True if the screen is currently being touched."""
        return self._touching
