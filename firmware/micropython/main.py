"""
copilot-buddy — ESP32-S3 desk pet for GitHub Copilot CLI (MicroPython).

Reads events from the host bridge over USB serial, maps them to
pet animation states, and renders the active pet on the display.
"""

import gc
import time

from config import ACTIVE_BOARD
from display_driver import init_display, set_backlight
from pet_renderer import PetAnimator
from serial_bridge import SerialBridge
from state_manager import STATE_BUSY, STATE_IDLE, STATE_SLEEP, StateManager

# ── Minimal fallback pet (used if octocat import fails) ─────────
_FALLBACK_PET = {
    "name": "fallback",
    "frames": {
        "idle": ["(* _ *)"],
        "sleep": ["(- _ -)  zzZ"],
        "busy": ["(*_*;)"],
        "attention": ["(*o* )!"],
        "celebrate": ["\\(^o^)/"],
        "dizzy": ["(@_@ )"],
        "heart": ["(<3_<3)"],
    },
}

# ── Demo mode state list (cycles when serial is unavailable) ────
_DEMO_STATES = [
    STATE_IDLE, STATE_BUSY, "attention", "celebrate",
    "dizzy", "heart", STATE_SLEEP,
]
_DEMO_HOLD_MS = 4000  # milliseconds per demo state


def _load_pet():
    """Import the default pet, fall back to minimal art on failure."""
    try:
        from pets.octocat import PET
        return PET
    except ImportError as exc:
        print("WARN: pet import failed:", exc)
        return _FALLBACK_PET


def main():
    """Entry point — initialise hardware and run the event loop."""
    print("copilot-buddy: starting (MicroPython)...")

    # ── Display ─────────────────────────────────────────────
    try:
        display = init_display(ACTIVE_BOARD)
    except RuntimeError as exc:
        print("FATAL: display init failed:", exc)
        while True:
            time.sleep_ms(1000)

    set_backlight(ACTIVE_BOARD, True)

    pet = _load_pet()
    print("Pet '{}' loaded".format(pet["name"]))

    # ── Serial bridge ───────────────────────────────────────
    bridge = SerialBridge(device_info={
        "pet": pet["name"],
        "display": ACTIVE_BOARD.get("display_type", "unknown"),
    })

    # ── State machine & animator ────────────────────────────
    sm = StateManager()
    animator = PetAnimator(display, pet, ACTIVE_BOARD, fps=2)
    animator.set_state(sm.state)

    prev_state = sm.state
    demo_idx = 0
    demo_last_ms = time.ticks_ms()
    gc_interval_ms = 30_000
    gc_last_ms = time.ticks_ms()

    # If select.poll is unavailable, run in demo mode
    try:
        import select  # noqa: F401
        demo_mode = False
        print("Serial bridge ready")
    except ImportError:
        demo_mode = True
        print("WARN: select unavailable — running in demo mode")

    print("Entering main loop...")

    # ── Main loop (~20 Hz) ──────────────────────────────────
    while True:
        now_ms = time.ticks_ms()

        # 1. Read serial
        if not demo_mode:
            msg = bridge.read_message()
            if msg is not None:
                sm.process_message(msg, now_ms)

        # 2. Demo-mode: cycle through states when no serial
        if demo_mode:
            if time.ticks_diff(now_ms, demo_last_ms) >= _DEMO_HOLD_MS:
                demo_idx = (demo_idx + 1) % len(_DEMO_STATES)
                sm.base_state = _DEMO_STATES[demo_idx]
                demo_last_ms = now_ms

        # 3. Tick state manager (timed expiry, disconnect check)
        cur = sm.update(now_ms)

        # 4. Push state changes to animator
        if cur != prev_state:
            animator.set_state(cur)
            prev_state = cur

        # 5. Build status text
        if sm.state == STATE_BUSY and sm.query:
            status = sm.query[:20]
        elif sm.disconnected:
            status = "~ disconnected ~"
        else:
            status = "q:{}".format(sm.queries_today) if sm.queries_today else ""

        # 6. Advance animation frame
        animator.update(now_ms, status_text=status)

        # 7. Periodic GC to reclaim memory
        if time.ticks_diff(now_ms, gc_last_ms) >= gc_interval_ms:
            gc.collect()
            gc_last_ms = now_ms

        time.sleep_ms(50)


main()
