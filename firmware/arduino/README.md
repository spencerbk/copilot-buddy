# copilot-buddy — Arduino / PlatformIO Port

C++ implementation of copilot-buddy for ESP32-S2 and ESP32-S3 boards, mirroring the
CircuitPython reference firmware.

## Prerequisites

- [PlatformIO CLI](https://docs.platformio.org/en/latest/core/) or
  [PlatformIO IDE](https://platformio.org/platformio-ide) (VS Code extension)

## Quick Start

```bash
cd firmware/arduino

# Build for the default board (ESP32-S3 DevKit + ST7789 240×240)
pio run -e devkit_st7789

# Flash
pio run -e devkit_st7789 -t upload

# Serial monitor
pio device monitor
```

## Board Selection

Choose your target by specifying the PlatformIO environment:

| Environment           | Board                       | Display            |
|-----------------------|-----------------------------|--------------------|
| `devkit_st7789`       | ESP32-S3 DevKit + ST7789    | 240×240 SPI TFT    |
| `devkit_ili9341`      | ESP32-S3 DevKit + ILI9341   | 240×320 SPI TFT    |
| `devkit_ssd1306`      | ESP32-S3 DevKit + SSD1306   | 128×64 I2C OLED    |
| `m5stickc_plus2`      | M5StickC Plus2              | 135×240 SPI TFT    |
| `lilygo_t_display_s3` | LILYGO T-Display-S3         | 170×320 SPI TFT    |
| `qtpy_s2_ssd1306`     | QT Py ESP32-S2 + SSD1306   | 128×64 I2C OLED    |
| `qtpy_s2_st7789`      | QT Py ESP32-S2 + ST7789    | 240×240 SPI TFT    |
| `qtpy_s2_ili9341`     | QT Py ESP32-S2 + ILI9341   | 240×320 SPI TFT    |
| `qtpy_s3_ssd1306`     | QT Py ESP32-S3 + SSD1306   | 128×64 I2C OLED    |
| `qtpy_s3_st7789`      | QT Py ESP32-S3 + ST7789    | 240×240 SPI TFT    |
| `qtpy_s3_ili9341`     | QT Py ESP32-S3 + ILI9341   | 240×320 SPI TFT    |

You can also edit `copilot_buddy/config.h` directly to uncomment a board
preset if you prefer building from the Arduino IDE.

## Pin Assignments

Pin assignments match the CircuitPython reference (`firmware/circuitpython/config.py`).
See `copilot_buddy/config.h` for the full mapping per board.

## Project Structure

```
firmware/arduino/
├── platformio.ini              # Build config (board environments)
├── README.md
└── copilot_buddy/
    ├── copilot_buddy.ino       # Main sketch
    ├── config.h                # Board presets & pin definitions
    ├── display.h / display.cpp # Display abstraction (TFT_eSPI / SSD1306)
    ├── state.h / state.cpp     # 7-state machine (port of state_manager.py)
    ├── pet.h / pet.cpp         # Pet animation renderer
    └── buddies/
        ├── octocat.h           # Octocat pet PROGMEM data
        ├── crab.h              # Crab pet
        ├── fox.h               # Fox pet
        ├── ghost.h             # Ghost pet
        ├── owl.h               # Owl pet
        └── robot.h             # Robot pet
```

## Regenerating Pet Data

Pet frame data is auto-generated from the CircuitPython pet modules.
To regenerate after modifying the Python pet files:

```bash
python tools/convert_pets.py            # all pets
python tools/convert_pets.py octocat    # specific pet
```

## Dependencies

Managed automatically by PlatformIO:

| Library          | Used For                              |
|------------------|---------------------------------------|
| ArduinoJson ^7   | Serial JSON parsing                   |
| TFT_eSPI ^2      | Color TFT display (ST7789, ILI9341)  |
| Adafruit SSD1306 | Monochrome OLED display               |
| Adafruit GFX     | Graphics primitives (SSD1306 backend) |

## Serial Protocol

The device reads newline-delimited JSON from USB serial at 115200 baud.
See `protocol/schema.md` for the full wire protocol specification.

## Known Limitations

- **Unicode rendering:** The default bitmap fonts (Adafruit GLCD) only
  cover ASCII 32–126. Non-ASCII characters in pet art (╱, ω, ♥, etc.)
  will render as blank or placeholder glyphs. For full Unicode support,
  load a TrueType font via TFT_eSPI's smooth font system or switch to
  the U8g2 library.
- **PROGMEM on ESP32:** `PROGMEM` is a no-op on ESP32 (const data is
  already stored in flash). The annotations are kept for documentation
  and AVR portability.
