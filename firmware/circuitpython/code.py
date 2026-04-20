"""
copilot-buddy — ESP32-S3 desk pet for GitHub Copilot CLI.

Reads events from the host bridge over USB serial, maps them to
pet animation states, and renders the active pet on the display.
"""

import gc
import time

import usb_cdc

from button import Button
from config import ACTIVE_BOARD
from display_driver import init_display, is_color_display, set_backlight
from pet_renderer import PetAnimator, create_pet_group, render_hud, render_stats_screen
from serial_bridge import SerialBridge
from state_manager import (
    STATE_BUSY,
    STATE_IDLE,
    STATE_SLEEP,
    StateManager,
)
from stats import Stats

# ── Pet roster ──────────────────────────────────────────────────
PET_NAMES = ["octocat", "crab", "fox", "owl", "robot", "ghost"]
_PET_SELECTION_PATH = "/pet_selection.txt"

# ── Minimal fallback pet (used if pet import fails) ─────────────
_FALLBACK_PET = {
    "name": "fallback",
    "frames": {
        "idle": ["(• _ •)"],
        "sleep": ["(- _ -)  zzZ"],
        "busy": ["(◎_◎;)"],
        "attention": ["(°o° )!"],
        "celebrate": ["\\(^o^)/"],
        "dizzy": ["(@_@ )"],
        "heart": ["(♥‿♥)"],
    },
}

# ── Demo mode state list (cycles when serial is unavailable) ────
_DEMO_STATES = [
    STATE_IDLE, STATE_BUSY, "attention", "celebrate",
    "dizzy", "heart", STATE_SLEEP,
]
_DEMO_HOLD = 4.0  # seconds per demo state

# ── Screen power ────────────────────────────────────────────────
_SCREEN_OFF_TIMEOUT = 30.0  # seconds of idle/sleep before backlight off

# States that count as "active" (keep screen on / wake it up)
_ACTIVE_STATES = frozenset(["busy", "attention", "celebrate", "dizzy", "heart"])


def _load_pet_by_name(name):
    """Dynamically load a pet module by name. Returns PET dict."""
    try:
        mod = __import__("pets." + name)
        return getattr(mod, name).PET
    except (ImportError, AttributeError) as exc:
        print("WARN: pet '{}' load failed: {}".format(name, exc))
        return None


def _load_saved_pet_index():
    """Read saved pet index from flash. Returns 0 on failure."""
    try:
        with open(_PET_SELECTION_PATH, "r") as f:
            idx = int(f.read().strip())
        if 0 <= idx < len(PET_NAMES):
            return idx
    except (OSError, ValueError):
        pass
    return 0


def _save_pet_index(idx):
    """Persist the current pet index to flash."""
    try:
        with open(_PET_SELECTION_PATH, "w") as f:
            f.write(str(idx))
    except OSError as exc:
        print("WARN: pet index save failed:", exc)


def main():
    """Entry point — initialise hardware and run the event loop."""
    print("copilot-buddy: starting...")

    # ── Display ─────────────────────────────────────────────
    try:
        display = init_display(ACTIVE_BOARD)
    except RuntimeError as exc:
        print("FATAL: display init failed:", exc)
        while True:
            time.sleep(1)

    set_backlight(ACTIVE_BOARD, True)
    color_display = is_color_display(ACTIVE_BOARD)

    # ── Pet loading ─────────────────────────────────────────
    pet_index = _load_saved_pet_index()
    pet = _load_pet_by_name(PET_NAMES[pet_index])
    if pet is None:
        pet = _FALLBACK_PET
        pet_index = 0

    group = create_pet_group(display, ACTIVE_BOARD)
    display.root_group = group
    print("Pet '{}' loaded".format(pet["name"]))

    # ── Serial bridge ───────────────────────────────────────
    serial_port = usb_cdc.data
    demo_mode = serial_port is None
    if demo_mode:
        print("WARN: usb_cdc.data is None — running in demo mode")
    else:
        print("Serial data port ready")

    bridge = SerialBridge(serial_port, device_info={
        "pet": pet["name"],
        "display": ACTIVE_BOARD.get("display_type", "unknown"),
    })

    # ── State machine & animator ────────────────────────────
    sm = StateManager()
    animator = PetAnimator(group, pet, fps=2)
    animator.set_state(sm.state)

    # ── Button, stats, screen power ─────────────────────────
    btn = Button(ACTIVE_BOARD)
    stats = Stats()
    stats_mode = False
    screen_on = True
    last_active_time = time.monotonic()
    bridge_ts = None  # latest unix timestamp from heartbeat

    # HUD scroll state
    hud_scroll = 0
    prev_entries_len = 0

    prev_state = sm.state
    demo_idx = 0
    demo_last = time.monotonic()
    gc_interval = 30.0
    gc_last = time.monotonic()

    print("Entering main loop...")

    # ── Main loop (~20 Hz) ──────────────────────────────────
    while True:
        now = time.monotonic()

        # 1. Read serial
        msg = bridge.read_message()
        if msg is not None:
            sm.process_message(msg, now)

            # Track bridge timestamp for stats date logic
            if isinstance(msg, dict):
                if "ts" in msg:
                    bridge_ts = msg["ts"]
                # Record query on "start" event
                if msg.get("evt") == "start":
                    stats.record_query(bridge_ts)

        # 2. Demo-mode: cycle through states when no serial
        if demo_mode:
            if now - demo_last >= _DEMO_HOLD:
                demo_idx = (demo_idx + 1) % len(_DEMO_STATES)
                sm.base_state = _DEMO_STATES[demo_idx]
                demo_last = now

        # 3. Tick state manager (timed expiry, disconnect check)
        cur = sm.update(now)

        # 4. Button handling
        btn_event = btn.update(now)
        if btn_event is not None:
            # Any button press wakes the screen
            if not screen_on:
                set_backlight(ACTIVE_BOARD, True)
                screen_on = True
                last_active_time = now
                # Consume the press — just wake, don't act
            elif stats_mode:
                # Any press in stats mode returns to pet mode
                stats_mode = False
                hud_scroll = 0
            elif btn_event == "short_press":
                # Scroll HUD transcript
                if sm.entries:
                    hud_scroll += 1
                    max_scroll = max(0, len(sm.entries) - 5)
                    if hud_scroll > max_scroll:
                        # Past end of entries → show stats
                        stats_mode = True
                        hud_scroll = 0
                else:
                    # No entries — short press shows stats
                    stats_mode = not stats_mode
            elif btn_event == "long_press":
                # Cycle to next pet
                pet_index = (pet_index + 1) % len(PET_NAMES)
                new_pet = _load_pet_by_name(PET_NAMES[pet_index])
                if new_pet is not None:
                    pet = new_pet
                    animator = PetAnimator(group, pet, fps=2)
                    animator.set_state(cur)
                    _save_pet_index(pet_index)
                    print("Pet switched to '{}'".format(pet["name"]))
                    gc.collect()
                else:
                    print("WARN: pet load failed, keeping current")

        # 5. Push state changes to animator
        if cur != prev_state:
            animator.set_state(cur)
            prev_state = cur

        # 6. Screen auto-off / wake logic
        if cur in _ACTIVE_STATES:
            last_active_time = now
            if not screen_on:
                set_backlight(ACTIVE_BOARD, True)
                screen_on = True
        elif screen_on and (now - last_active_time >= _SCREEN_OFF_TIMEOUT):
            set_backlight(ACTIVE_BOARD, False)
            screen_on = False

        # 7. Reset scroll when new entries arrive
        cur_entries_len = len(sm.entries)
        if cur_entries_len != prev_entries_len:
            hud_scroll = 0
            prev_entries_len = cur_entries_len

        # 8. Render: stats screen or pet animation + HUD
        if stats_mode:
            gc.collect()
            render_stats_screen(
                group,
                pet["name"],
                stats.queries_today,
                stats.total_queries,
                now,
                gc.mem_free(),
                color_display,
            )
        else:
            # Advance pet animation frame
            animator.update(now)

            # Render HUD transcript
            render_hud(group, sm.entries, sm.msg, hud_scroll)

        # 9. Periodic stats save
        stats.save()

        # 10. Periodic GC to reclaim memory
        if now - gc_last >= gc_interval:
            gc.collect()
            gc_last = now

        time.sleep(0.05)


main()
