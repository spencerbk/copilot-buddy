"""Pet renderer for copilot-buddy (MicroPython).

Renders ASCII pet frames directly to the display driver.
Supports colour TFT (ST7789/ILI9341 via st7789_mpy) and
monochrome OLED (SSD1306 via framebuf).

No displayio — all rendering is direct driver calls.
"""

import time

# Built-in framebuf font is 8×8 pixels for SSD1306.
# ST7789 MicroPython driver uses its own font via display.text().
_OLED_FONT_H = 8
_OLED_FONT_W = 8

# Approximate character size for ST7789 built-in font
_TFT_FONT_H = 8
_TFT_FONT_W = 8


def _is_oled(config):
    """Return True if the display is an SSD1306 OLED."""
    return config.get("display_type") == "SSD1306"


class PetAnimator:
    """Drives frame-cycling animation for a pet on a display."""

    def __init__(self, display, pet_data, config, fps=2):
        """Create an animator.

        Args:
            display: Initialised display object (ST7789/ILI9341/SSD1306).
            pet_data: PET dict from a pets/*.py module.
            config: Board config dict with 'width', 'height', etc.
            fps: Target frames per second for animation.
        """
        self._display = display
        self._pet = pet_data
        self._config = config
        self._oled = _is_oled(config)
        self._width = config["width"]
        self._height = config["height"]
        self._fps = fps
        self._frame_interval_ms = 1000 // fps
        self._current_state = "idle"
        self._frame_index = 0
        self._last_frame_ms = 0
        self._last_status = ""

    def set_state(self, state):
        """Change pet state.  Resets frame index and renders immediately."""
        if state != self._current_state:
            self._current_state = state
            self._frame_index = 0
            self._render_current()

    def update(self, now_ms, status_text=""):
        """Advance the animation frame if the interval has elapsed.

        *now_ms* should be ``time.ticks_ms()``.
        """
        elapsed = time.ticks_diff(now_ms, self._last_frame_ms)
        if elapsed < self._frame_interval_ms:
            return
        frames = self._pet["frames"].get(self._current_state, [])
        if frames:
            self._frame_index = (self._frame_index + 1) % len(frames)
            self._render_current(status_text)
        self._last_frame_ms = now_ms

    def _render_current(self, status_text=""):
        """Render the current frame to the display."""
        frames = self._pet["frames"].get(self._current_state, [])
        if not frames:
            return
        idx = min(self._frame_index, len(frames) - 1)
        frame_text = frames[idx]

        if self._oled:
            self._render_oled(frame_text, status_text)
        else:
            self._render_tft(frame_text, status_text)

    def _render_oled(self, frame_text, status_text):
        """Render to SSD1306 OLED using framebuf text."""
        display = self._display
        display.fill(0)

        lines = frame_text.split("\n")
        # Center pet art vertically above status line
        status_reserve = _OLED_FONT_H + 2 if status_text else 0
        avail_h = self._height - status_reserve
        art_h = len(lines) * _OLED_FONT_H
        y_start = max(0, (avail_h - art_h) // 2)

        # Estimate max line width for horizontal centering
        max_w = max((len(ln) for ln in lines), default=0)
        art_w = max_w * _OLED_FONT_W
        x_start = max(0, (self._width - art_w) // 2)

        for i, line in enumerate(lines):
            display.text(line, x_start, y_start + i * _OLED_FONT_H, 1)

        # Status text at the bottom
        if status_text:
            status_y = self._height - _OLED_FONT_H
            display.text(status_text[:16], 0, status_y, 1)

        display.show()

    def _render_tft(self, frame_text, status_text):
        """Render to colour TFT (ST7789/ILI9341) using driver text method.

        The st7789_mpy driver provides ``display.text(font, string, x, y)``
        and a built-in ``font`` attribute or requires an external font module.
        We use a simple approach compatible with the common st7789_mpy API.
        """
        display = self._display

        # Import colour constants — st7789 driver exposes them
        white = 0xFFFF
        black = 0x0000

        display.fill(black)

        lines = frame_text.split("\n")
        # Center vertically
        status_reserve = _TFT_FONT_H + 4 if status_text else 0
        avail_h = self._height - status_reserve
        art_h = len(lines) * _TFT_FONT_H
        y_start = max(0, (avail_h - art_h) // 2)

        max_w = max((len(ln) for ln in lines), default=0)
        art_w = max_w * _TFT_FONT_W
        x_start = max(2, (self._width - art_w) // 2)

        for i, line in enumerate(lines):
            # st7789_mpy text method: display.text(font, string, x, y, color)
            # If no font attr, fall back to a simple positional write
            try:
                display.text(
                    display.font, line,
                    x_start, y_start + i * _TFT_FONT_H,
                    white,
                )
            except (AttributeError, TypeError):
                # Fallback: some drivers use text(string, x, y, color)
                try:
                    display.text(
                        line,
                        x_start, y_start + i * _TFT_FONT_H,
                        white,
                    )
                except TypeError:
                    pass  # skip if text method is incompatible

        # Status text at the bottom
        if status_text:
            status_y = self._height - _TFT_FONT_H - 2
            try:
                display.text(
                    display.font, status_text[:24],
                    2, status_y, white,
                )
            except (AttributeError, TypeError):
                try:
                    display.text(status_text[:24], 2, status_y, white)
                except TypeError:
                    pass
