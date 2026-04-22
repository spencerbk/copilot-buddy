"""Button handler for copilot-buddy.

Handles short press (scroll HUD) and long press (cycle pet).
Debounced with software debounce.
"""

import digitalio


# Thresholds (seconds)
_DEBOUNCE_S = 0.05
_LONG_PRESS_S = 2.0


class Button:
    """Debounced button with short-press and long-press detection."""

    def __init__(self, config):
        pin = config.get("button_pin")
        if pin is None:
            self._pin = None
            return

        self._active_low = config.get("button_active_low", True)
        self._pin = digitalio.DigitalInOut(pin)
        self._pin.direction = digitalio.Direction.INPUT
        if self._active_low:
            self._pin.pull = digitalio.Pull.UP
        else:
            self._pin.pull = digitalio.Pull.DOWN

        self._pressed = False
        self._press_start = 0.0
        self._last_change = 0.0

    def update(self, now):
        """Poll the button and return an event string or None.

        Returns:
            "short_press" — released after <2 s hold.
            "long_press"  — released after >=2 s hold.
            None          — no event this tick.
        """
        if self._pin is None:
            return None

        raw = not self._pin.value if self._active_low else self._pin.value

        # Debounce: ignore transitions within 50 ms of last change
        if raw != self._pressed:
            if now - self._last_change < _DEBOUNCE_S:
                return None
            self._last_change = now

            if raw:
                # Button just pressed
                self._pressed = True
                self._press_start = now
            else:
                # Button just released — determine press type
                self._pressed = False
                held = now - self._press_start
                if held >= _LONG_PRESS_S:
                    return "long_press"
                return "short_press"

        return None

    @property
    def is_pressed(self):
        """Return True if the button is currently held down."""
        return self._pressed
