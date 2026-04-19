"""Pet renderer for copilot-buddy.

Renders ASCII pet frames to the display using displayio.
Reuses label objects to minimize memory allocations.
"""

import displayio
import terminalio
from adafruit_display_text import label

# Label indices within the pet group
_PET_LABEL = 0
_STATUS_LABEL = 1

# Built-in font character size (terminalio.FONT is 6x12 pixels)
_FONT_W = 6
_FONT_H = 12


def create_pet_group(display, config):
    """Create a displayio Group with pet and status labels.

    Labels are created once and reused — update via render_frame().

    Args:
        display: Initialized displayio.Display.
        config: Board config dict with 'width' and 'height'.

    Returns:
        displayio.Group containing pet art and status text labels.
    """
    w = config["width"]
    h = config["height"]

    group = displayio.Group()

    # Estimate pet art size for centering (typical: ~14 chars wide, 4 lines)
    est_art_w = 14 * _FONT_W
    est_art_h = 4 * _FONT_H

    # Horizontal: roughly center the art block
    pet_x = max(2, (w - est_art_w) // 2)

    # Vertical: center pet in the area above the status line
    status_reserve = _FONT_H + 4
    avail_h = h - status_reserve
    # y is vertical center of first text line
    pet_y = max(_FONT_H // 2, (avail_h - est_art_h) // 2 + _FONT_H // 2)

    pet_label = label.Label(
        terminalio.FONT,
        text="",
        color=0xFFFFFF,
        x=pet_x,
        y=pet_y,
    )
    group.append(pet_label)

    # Status label pinned to the bottom of the screen
    status_y = h - _FONT_H // 2 - 2
    status_label = label.Label(
        terminalio.FONT,
        text="",
        color=0xFFFFFF,
        x=pet_x,
        y=status_y,
    )
    group.append(status_label)

    return group


def render_frame(group, frame_text, status_text=""):
    """Update the displayed pet frame and status text.

    Updates existing label objects in-place — no new allocations.

    Args:
        group: displayio.Group from create_pet_group().
        frame_text: Multi-line ASCII art string for the pet.
        status_text: Text shown below pet. Empty string clears it.
    """
    group[_PET_LABEL].text = frame_text
    group[_STATUS_LABEL].text = status_text


def render_stats_screen(group, pet_name, queries_today, total_queries,
                        uptime_s, heap_free, is_color):
    """Render the stats info screen (replaces pet art temporarily).

    Updates existing label objects — no new allocations.

    Args:
        group: displayio.Group from create_pet_group().
        pet_name: Name of the active pet.
        queries_today: Daily query count.
        total_queries: Lifetime query count.
        uptime_s: Device uptime in seconds (monotonic).
        heap_free: Free heap bytes from gc.mem_free().
        is_color: True for TFT displays (more room for text).
    """
    hrs = int(uptime_s) // 3600
    mins = (int(uptime_s) % 3600) // 60

    if is_color:
        text = (
            "-- stats --\n"
            "pet: {}\n"
            "today: {}\n"
            "total: {}\n"
            "up: {}h {}m\n"
            "heap: {}".format(
                pet_name, queries_today, total_queries,
                hrs, mins, heap_free,
            )
        )
    else:
        # Compact for small OLED screens
        text = (
            "q:{}/{}\n"
            "up:{}h{}m\n"
            "hp:{}".format(
                queries_today, total_queries,
                hrs, mins, heap_free,
            )
        )

    group[_PET_LABEL].text = text
    group[_STATUS_LABEL].text = ""


def clear_display(display):
    """Clear the display by showing an empty group."""
    display.root_group = displayio.Group()


# ── animator ────────────────────────────────────────────────────


class PetAnimator:
    """Drives frame-cycling animation for a pet on a displayio Group."""

    def __init__(self, group, pet_data, fps=2):
        """Create an animator.

        Args:
            group: displayio.Group from create_pet_group().
            pet_data: PET dict from a pets/*.py module.
            fps: target frames per second for animation.
        """
        self._group = group
        self._pet = pet_data
        self._fps = fps
        self._frame_interval = 1.0 / fps
        self._current_state = "idle"
        self._frame_index = 0
        self._last_frame_time = 0.0

    def set_state(self, state):
        """Change pet state.  Resets frame index and renders immediately."""
        if state != self._current_state:
            self._current_state = state
            self._frame_index = 0
            self._render_current()

    def update(self, now, status_text=""):
        """Advance the animation frame if the interval has elapsed."""
        if now - self._last_frame_time < self._frame_interval:
            return
        frames = self._pet["frames"].get(self._current_state, [])
        if frames:
            self._frame_index = (self._frame_index + 1) % len(frames)
            render_frame(self._group, frames[self._frame_index], status_text)
        self._last_frame_time = now

    def _render_current(self):
        frames = self._pet["frames"].get(self._current_state, [])
        if frames:
            idx = min(self._frame_index, len(frames) - 1)
            render_frame(self._group, frames[idx])
