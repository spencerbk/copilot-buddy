# Roadmap

## Planned

*(Nothing currently — suggest new features via issues.)*

## Done

### Capacitive touch input support

Added `touch_input.py` — a `TouchInput` class that drives the FT6206/FT6236
capacitive touch controller via STEMMA QT I2C. Gesture detection maps tap to
`"short_press"` (scroll HUD) and horizontal swipe to `"long_press"` (cycle
pet). Raw touch coordinates are mapped to logical display coordinates
accounting for display rotation. Gracefully degrades if the touch controller
is not present. Added `touch_i2c_addr`, `touch_sda`, `touch_scl` to the
EYESPI BFF board config. Requires `adafruit_focaltouch` and
`adafruit_bus_device` from the Adafruit CircuitPython Bundle.

### HUD transcript with repo-prefixed activity log

Implemented a claude-desktop-buddy-style HUD transcript at the bottom of the
display. Shows 5 lines of recent Copilot activity, each formatted as
`"repo HH:MM query"`. Font rendered at 2× scale for readability on the
ILI9341. Newest entry is bright white; older entries dimmed gray. Scrollable
via button short-press. Bridge builds entries from both the process watcher
and the CLI file watcher.

### Serial & transport fixes

- Fixed `serial_bridge.py` `bytearray.find()` to use `b"\n"` instead of
  `ord("\n")` (CircuitPython TypeError).
- Fixed `serial_bridge.py` bytearray slice deletion — CircuitPython doesn't
  support `del buf[start:stop]`; replaced with reassignment.
- Fixed `transport_serial.py` auto-detect: added 300 ms USB CDC settle delay
  and `reset_input_buffer()` after opening port for reliable handshake.
- Fixed `boot.py` USB endpoint overflow: disabled HID, MIDI, and USB storage
  before enabling dual CDC (`console=True, data=True`).

### Standalone CLI per-turn detection

Added `bridge/cli_watcher.py` — a file-based watcher that detects per-turn
activity in the standalone `copilot` CLI by watching `~/.copilot/` files.
`command-history-state.json` modifications signal turn starts (with query
text); `session-state/*/events.jsonl` quiescence signals turn ends. Supports
multiple simultaneous sessions. Integrated into the bridge alongside the
existing process-based watcher. New `mode: "chat"` in the wire protocol.

### Eye SPI BFF board config

Verified that the Adafruit EYESPI BFF routes TFT CS to TX and TFT DC to RX,
with RST and backlight not connected (through-hole solder pads). Added
`_qtpy_s2_eyespi_ili9341()` board config to
`firmware/circuitpython/config.py` and documented the wiring in
`docs/wiring.md`. Board configs were later refactored to lazy factory
functions so pin references are only evaluated for the active board.
