# CircuitPython Firmware

The recommended firmware for copilot-buddy. Easiest to set up and modify.

## Requirements

- ESP32-S3 board with a supported display (see [docs/wiring.md](../../docs/wiring.md))
- [CircuitPython 9.x](https://circuitpython.org/downloads) flashed to the board
- Adafruit CircuitPython libraries (see below)

## Required Libraries

Install these to the `CIRCUITPY/lib/` folder. Download from the
[Adafruit CircuitPython Bundle](https://circuitpython.org/libraries):

| Library | Used for |
|---------|----------|
| `adafruit_display_text` | Text rendering on displays |
| `adafruit_st7789` | ST7789 TFT displays |
| `adafruit_ili9341` | ILI9341 TFT displays (if using) |
| `adafruit_ssd1306` | SSD1306 OLED displays (if using) |

Only install the display driver for your specific display.

## Setup

1. **Flash CircuitPython** to your ESP32-S3 board
2. **Install libraries** — copy the required `.mpy` files to `CIRCUITPY/lib/`
3. **Edit `config.py`** — uncomment the line matching your board:
   ```python
   ACTIVE_BOARD = BOARD_DEVKIT_ST7789  # ← change this
   ```
4. **Copy all files** from this directory to `CIRCUITPY/`:
   ```
   CIRCUITPY/
   ├── boot.py
   ├── code.py
   ├── config.py
   ├── display_driver.py
   ├── serial_bridge.py
   ├── state_manager.py
   ├── pet_renderer.py
   ├── stats.py
   ├── button.py
   └── pets/
       ├── __init__.py
       ├── octocat.py
       ├── crab.py
       ├── fox.py
       ├── owl.py
       ├── robot.py
       └── ghost.py
   ```
5. **Hard reset** the board (press reset button or power cycle)

   > `boot.py` enables the USB CDC data port. It only runs on hard reset,
   > not on soft reload (Ctrl+D). After the first flash, you **must**
   > hard reset for serial communication to work.

6. **Run the bridge** on your computer (see `bridge/README.md`)

## Troubleshooting

### "usb_cdc.data is None"
`boot.py` hasn't taken effect yet. Hard reset the board (press the physical reset button).

### Display shows nothing
- Check wiring against [docs/wiring.md](../../docs/wiring.md)
- Verify the correct display library is installed in `CIRCUITPY/lib/`
- Check `config.py` has the right board selected

### Safe mode recovery
If `boot.py` causes issues, hold the **BOOT** button during reset to enter safe mode. Then delete or rename `boot.py` from the CIRCUITPY drive.

### Serial port not detected by bridge
- The board exposes **two** serial ports: Console (REPL) and Data
- The bridge connects to the **Data** port
- If auto-detect fails, try specifying the port explicitly: `--port COM4`

## Demo Mode

If the USB data serial port is not available (boot.py not configured), the firmware runs in **demo mode** — cycling through all pet states automatically. This is useful for testing the display without the bridge.
