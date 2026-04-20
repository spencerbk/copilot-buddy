"""Pet renderer for copilot-buddy.

Renders ASCII pet frames to the display using displayio.
Reuses label objects to minimize memory allocations.

Group layout (stable indices):
  0 — solid background (black for TFT displays)
  1 — pet art label (ASCII frames)
  2 — HUD line 1 (newest entry, bright white, scale 2×)
  3 — HUD line 2
  4 — HUD line 3
  5 — HUD line 4
  6 — HUD line 5 (oldest visible, dimmed gray)
"""

import displayio
import terminalio
from adafruit_display_text import label

# Label indices within the pet group
_PET_LABEL = 1
_HUD_LINE_1 = 2
_HUD_LINE_2 = 3
_HUD_LINE_3 = 4
_HUD_LINE_4 = 5
_HUD_LINE_5 = 6

# Built-in font character size (terminalio.FONT is 6x12 pixels)
_FONT_W = 6
_FONT_H = 12

# HUD area config
_HUD_LINES = 5
_HUD_FONT_SCALE = 2
_SCALED_FONT_H = _FONT_H * _HUD_FONT_SCALE  # 24px per line
_HUD_AREA_H = _HUD_LINES * _SCALED_FONT_H + 10  # 130px total
_HUD_COLOR_BRIGHT = 0xFFFFFF
_HUD_COLOR_DIM = 0x888888


def create_pet_group(display, config):
    """Create a displayio Group with pet and HUD labels.

    Labels are created once and reused — update via render_frame() / render_hud().

    Args:
        display: Initialized displayio.Display.
        config: Board config dict with 'width' and 'height'.

    Returns:
        displayio.Group containing background, pet art, and HUD labels.
    """
    w = display.width
    h = display.height

    group = displayio.Group()

    # 0: Solid black background
    bg_bitmap = displayio.Bitmap(w, h, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0x000000
    group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

    # Pet area: everything above the HUD
    pet_area_h = h - _HUD_AREA_H
    est_art_w = 14 * _FONT_W
    est_art_h = 4 * _FONT_H

    pet_x = max(2, (w - est_art_w) // 2)
    pet_y = max(_FONT_H // 2, (pet_area_h - est_art_h) // 2 + _FONT_H // 2)

    # 1: Pet label
    pet_label = label.Label(
        terminalio.FONT,
        text="",
        color=0xFFFFFF,
        x=pet_x,
        y=pet_y,
    )
    group.append(pet_label)

    # 2-6: HUD lines (bottom of screen, scale 2× for readability)
    hud_x = 2
    hud_base_y = h - _HUD_AREA_H + _SCALED_FONT_H // 2 + 2

    for i in range(_HUD_LINES):
        color = _HUD_COLOR_BRIGHT if i == 0 else _HUD_COLOR_DIM
        hud_label = label.Label(
            terminalio.FONT,
            text="",
            color=color,
            x=hud_x,
            y=hud_base_y + i * _SCALED_FONT_H,
        )
        hud_label.scale = _HUD_FONT_SCALE
        group.append(hud_label)

    return group


def render_frame(group, frame_text):
    """Update the displayed pet frame.

    Updates existing label object in-place — no new allocations.

    Args:
        group: displayio.Group from create_pet_group().
        frame_text: Multi-line ASCII art string for the pet.
    """
    group[_PET_LABEL].text = frame_text


def render_hud(group, entries, msg, scroll_offset=0):
    """Update the HUD transcript area.

    Args:
        group: displayio.Group from create_pet_group().
        entries: List of timestamped activity strings (newest first).
        msg: One-line summary shown when no entries.
        scroll_offset: Number of entries to skip from newest (0 = show newest).
    """
    if not entries:
        # No entries — show summary message
        group[_HUD_LINE_1].text = msg
        group[_HUD_LINE_1].color = _HUD_COLOR_DIM
        for j in range(1, _HUD_LINES):
            group[_HUD_LINE_1 + j].text = ""
        return

    n = len(entries)
    # Clamp scroll offset
    max_scroll = max(0, n - _HUD_LINES)
    if scroll_offset > max_scroll:
        scroll_offset = max_scroll

    for i in range(_HUD_LINES):
        idx = scroll_offset + i
        hud_label = group[_HUD_LINE_1 + i]
        if idx < n:
            hud_label.text = entries[idx]
            # Newest visible line is bright, rest dimmed
            hud_label.color = _HUD_COLOR_BRIGHT if i == 0 and scroll_offset == 0 else _HUD_COLOR_DIM
        else:
            hud_label.text = ""

    # Scroll indicator on last line when scrolled
    if scroll_offset > 0:
        last = group[_HUD_LINE_1 + _HUD_LINES - 1]
        existing = last.text
        if existing:
            max_w = 26  # must match MAX_ENTRY_LEN in bridge/constants.py
            last.text = existing[:max_w - 3] + " -" + str(scroll_offset)


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
        text = (
            "q:{}/{}\n"
            "up:{}h{}m\n"
            "hp:{}".format(
                queries_today, total_queries,
                hrs, mins, heap_free,
            )
        )

    group[_PET_LABEL].text = text
    # Clear HUD lines during stats display
    for j in range(_HUD_LINES):
        group[_HUD_LINE_1 + j].text = ""


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

    def update(self, now):
        """Advance the animation frame if the interval has elapsed."""
        if now - self._last_frame_time < self._frame_interval:
            return
        frames = self._pet["frames"].get(self._current_state, [])
        if frames:
            self._frame_index = (self._frame_index + 1) % len(frames)
            render_frame(self._group, frames[self._frame_index])
        self._last_frame_time = now

    def _render_current(self):
        frames = self._pet["frames"].get(self._current_state, [])
        if frames:
            idx = min(self._frame_index, len(frames) - 1)
            render_frame(self._group, frames[idx])
