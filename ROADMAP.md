# Roadmap

## Planned

### Capacitive touch input support

Add an I2C capacitive-touch driver (FT6206 / FT6236) for the Adafruit 2.8"
TFT ILI9341 breakout. The touch controller can connect over the STEMMA QT
connector on the QT Py ESP32-S2. The EYESPI BFF exposes the touch IRQ pin
on A0 and touch CS on A1. This would replace or supplement the current
single-button input with tap and swipe gestures for cycling pets, opening
stats, and other interactions.

## Done

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
