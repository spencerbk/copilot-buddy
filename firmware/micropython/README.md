# copilot-buddy — MicroPython Port

Minimal port of the CircuitPython copilot-buddy firmware to **MicroPython** for ESP32-S2 and ESP32-S3 boards.

## Prerequisites

- ESP32-S2 or ESP32-S3 board with a supported display (ST7789, ILI9341, or SSD1306)
- MicroPython firmware for your chip variant:
  - [ESP32-S3](https://micropython.org/download/ESP32_GENERIC_S3/)
  - [ESP32-S2](https://micropython.org/download/ESP32_GENERIC_S2/)

## Flash MicroPython

```bash
# Erase flash (one-time) — use esp32s2 or esp32s3 to match your chip
esptool.py --chip esp32s3 erase_flash

# Flash MicroPython firmware
esptool.py --chip esp32s3 --port COMx write_flash -z 0x0 ESP32_GENERIC_S3-xxxxxxxx-vX.X.X.bin
```

## Install Required Libraries

Use `mpremote` to install display drivers:

```bash
# For ST7789 TFT displays
mpremote mip install github:russhughes/st7789_mpy

# For SSD1306 OLED displays (included in micropython-lib)
mpremote mip install ssd1306

# For ILI9341 TFT displays
mpremote mip install github:rdagger/micropython-ili9341
```

## Deploy Files

Copy all project files to the board:

```bash
mpremote cp config.py :
mpremote cp display_driver.py :
mpremote cp serial_bridge.py :
mpremote cp state_manager.py :
mpremote cp pet_renderer.py :
mpremote cp main.py :
mpremote mkdir :pets
mpremote cp pets/__init__.py :pets/
mpremote cp pets/octocat.py :pets/
mpremote cp pets/crab.py :pets/
mpremote cp pets/fox.py :pets/
mpremote cp pets/ghost.py :pets/
mpremote cp pets/owl.py :pets/
mpremote cp pets/robot.py :pets/
```

## Configure Your Board

Edit `config.py` and uncomment the line matching your hardware:

```python
# ACTIVE_BOARD = BOARD_M5STICKC_PLUS2
# ACTIVE_BOARD = BOARD_LILYGO_T_DISPLAY_S3
# ACTIVE_BOARD = BOARD_DEVKIT_SSD1306
ACTIVE_BOARD = BOARD_DEVKIT_ST7789         # ← default
# ACTIVE_BOARD = BOARD_DEVKIT_ILI9341
# ACTIVE_BOARD = BOARD_QTPY_S2_SSD1306
# ACTIVE_BOARD = BOARD_QTPY_S2_ST7789
# ACTIVE_BOARD = BOARD_QTPY_S2_ILI9341
# ACTIVE_BOARD = BOARD_QTPY_S3_SSD1306
# ACTIVE_BOARD = BOARD_QTPY_S3_ST7789
# ACTIVE_BOARD = BOARD_QTPY_S3_ILI9341
```

Then re-upload: `mpremote cp config.py :`

## How It Works

1. **main.py** is the entry point (MicroPython auto-runs this on boot)
2. Initialises the display via `display_driver.py`
3. Loads pet ASCII art from `pets/octocat.py`
4. Reads JSON events from USB serial via `serial_bridge.py`
5. Maps events to pet states via `state_manager.py`
6. Renders animated frames via `pet_renderer.py`

If no serial connection is detected, the firmware runs in **demo mode**, cycling through all pet states automatically.

## Key Differences from CircuitPython

| Feature | CircuitPython | MicroPython |
|---|---|---|
| Display API | `displayio` framework | Direct driver calls |
| Pin access | `board.IOxx` objects | `machine.Pin(n)` integers |
| SPI/I2C | `busio.SPI` / `busio.I2C` | `machine.SPI` / `machine.I2C` |
| USB Serial | `usb_cdc.data` | `sys.stdin` / `sys.stdout` |
| Timing | `time.monotonic()` | `time.ticks_ms()` / `time.ticks_diff()` |
| Entry point | `code.py` | `main.py` |
| JSON | `json` | `ujson` (or `json`) |

## Troubleshooting

- **Display not working**: Verify pin numbers in `config.py` match your wiring. Check that the display driver library is installed.
- **No serial data**: Ensure the host bridge is sending newline-delimited JSON. Check USB connection.
- **Import errors**: Make sure all library dependencies are installed on the board (see Install section above).
- **Out of memory**: Use a pet with simpler ASCII art, or reduce animation FPS in `main.py`.
