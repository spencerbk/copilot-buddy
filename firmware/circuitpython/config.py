"""Board adapter configuration for copilot-buddy.

Edit ACTIVE_BOARD below to match your hardware, then save.
Each adapter dict contains all the pin assignments, display parameters,
and bus settings needed to initialize the board.

This is the ONLY file you need to edit for your hardware.
"""

import board


# ──── Board Adapters ────────────────────────────────────────────

BOARD_M5STICKC_PLUS2 = {
    "name": "M5StickC Plus2",
    "display_type": "ST7789",
    "width": 135,
    "height": 240,
    "rotation": 90,
    # SPI pins (M5Stack standard)
    "sck": board.IO13,
    "mosi": board.IO15,
    "cs": board.IO5,
    "dc": board.IO23,
    "rst": board.IO18,
    "bl": board.IO27,
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 40_000_000,
    "color_order": "BGR",
    "colstart": 52,
    "rowstart": 40,
    # Button A (front)
    "button_pin": board.IO37,
    "button_active_low": True,
}

BOARD_LILYGO_T_DISPLAY_S3 = {
    "name": "LILYGO T-Display-S3",
    "display_type": "ST7789",
    "width": 170,
    "height": 320,
    "rotation": 0,
    # SPI pins (LILYGO standard)
    "sck": board.IO12,
    "mosi": board.IO11,
    "cs": board.IO10,
    "dc": board.IO13,
    "rst": board.IO9,
    "bl": board.IO38,
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 40_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # Button 1 (left, active low)
    "button_pin": board.IO0,
    "button_active_low": True,
}

BOARD_DEVKIT_SSD1306 = {
    "name": "ESP32-S3 DevKit + SSD1306",
    "display_type": "SSD1306",
    "width": 128,
    "height": 64,
    "rotation": 0,
    # I2C pins (spec defaults)
    "sda": board.IO13,
    "scl": board.IO14,
    "i2c_addr": 0x3C,
    "bus_frequency": 400_000,
    # No backlight on OLED
    "bl": None,
    "bl_active_high": False,
    "bl_pwm": False,
    "color_order": None,
    "colstart": 0,
    "rowstart": 0,
    # User button (active low with pull-up)
    "button_pin": board.IO0,
    "button_active_low": True,
}

BOARD_DEVKIT_ST7789 = {
    "name": "ESP32-S3 DevKit + ST7789",
    "display_type": "ST7789",
    "width": 240,
    "height": 240,
    "rotation": 0,
    # SPI pins (spec defaults)
    "sck": board.IO14,
    "mosi": board.IO13,
    "cs": board.IO10,
    "dc": board.IO9,
    "rst": board.IO8,
    "bl": board.IO7,
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # User button (active low with pull-up)
    "button_pin": board.IO0,
    "button_active_low": True,
}

BOARD_DEVKIT_ILI9341 = {
    "name": "ESP32-S3 DevKit + ILI9341",
    "display_type": "ILI9341",
    "width": 240,
    "height": 320,
    "rotation": 0,
    # SPI pins (spec defaults)
    "sck": board.IO14,
    "mosi": board.IO13,
    "cs": board.IO10,
    "dc": board.IO9,
    "rst": board.IO8,
    "bl": board.IO7,
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # User button (active low with pull-up)
    "button_pin": board.IO0,
    "button_active_low": True,
}

BOARD_QTPY_S2_SSD1306 = {
    "name": "QT Py ESP32-S2 + SSD1306",
    "display_type": "SSD1306",
    "width": 128,
    "height": 64,
    "rotation": 0,
    # STEMMA QT I2C pins
    "sda": board.SDA1,      # STEMMA QT connector (GPIO 41)
    "scl": board.SCL1,      # STEMMA QT connector (GPIO 40)
    "i2c_addr": 0x3C,
    "bus_frequency": 400_000,
    # No backlight on OLED
    "bl": None,
    "bl_active_high": False,
    "bl_pwm": False,
    "color_order": None,
    "colstart": 0,
    "rowstart": 0,
    # Built-in BOOT button (active low)
    "button_pin": board.BUTTON,
    "button_active_low": True,
}

BOARD_QTPY_S2_ST7789 = {
    "name": "QT Py ESP32-S2 + ST7789",
    "display_type": "ST7789",
    "width": 240,
    "height": 240,
    "rotation": 0,
    # SPI pins
    "sck": board.SCK,       # GPIO 36
    "mosi": board.MOSI,     # GPIO 35
    "cs": board.A0,         # GPIO 18
    "dc": board.A1,         # GPIO 17
    "rst": board.A2,        # GPIO 9
    "bl": board.A3,         # GPIO 8
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # Built-in BOOT button (active low)
    "button_pin": board.BUTTON,
    "button_active_low": True,
}

BOARD_QTPY_S2_ILI9341 = {
    "name": "QT Py ESP32-S2 + ILI9341",
    "display_type": "ILI9341",
    "width": 240,
    "height": 320,
    "rotation": 0,
    # SPI pins
    "sck": board.SCK,       # GPIO 36
    "mosi": board.MOSI,     # GPIO 35
    "cs": board.A0,         # GPIO 18
    "dc": board.A1,         # GPIO 17
    "rst": board.A2,        # GPIO 9
    "bl": board.A3,         # GPIO 8
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # Built-in BOOT button (active low)
    "button_pin": board.BUTTON,
    "button_active_low": True,
}

BOARD_QTPY_S3_SSD1306 = {
    "name": "QT Py ESP32-S3 + SSD1306",
    "display_type": "SSD1306",
    "width": 128,
    "height": 64,
    "rotation": 0,
    # STEMMA QT I2C pins
    "sda": board.SDA1,      # STEMMA QT connector (GPIO 41)
    "scl": board.SCL1,      # STEMMA QT connector (GPIO 40)
    "i2c_addr": 0x3C,
    "bus_frequency": 400_000,
    # No backlight on OLED
    "bl": None,
    "bl_active_high": False,
    "bl_pwm": False,
    "color_order": None,
    "colstart": 0,
    "rowstart": 0,
    # Built-in BOOT button (active low)
    "button_pin": board.BUTTON,
    "button_active_low": True,
}

BOARD_QTPY_S3_ST7789 = {
    "name": "QT Py ESP32-S3 + ST7789",
    "display_type": "ST7789",
    "width": 240,
    "height": 240,
    "rotation": 0,
    # SPI pins
    "sck": board.SCK,       # GPIO 36
    "mosi": board.MOSI,     # GPIO 35
    "cs": board.A0,         # GPIO 18
    "dc": board.A1,         # GPIO 17
    "rst": board.A2,        # GPIO 9
    "bl": board.A3,         # GPIO 8
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # Built-in BOOT button (active low)
    "button_pin": board.BUTTON,
    "button_active_low": True,
}

BOARD_QTPY_S3_ILI9341 = {
    "name": "QT Py ESP32-S3 + ILI9341",
    "display_type": "ILI9341",
    "width": 240,
    "height": 320,
    "rotation": 0,
    # SPI pins
    "sck": board.SCK,       # GPIO 36
    "mosi": board.MOSI,     # GPIO 35
    "cs": board.A0,         # GPIO 18
    "dc": board.A1,         # GPIO 17
    "rst": board.A2,        # GPIO 9
    "bl": board.A3,         # GPIO 8
    "bl_active_high": True,
    "bl_pwm": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # Built-in BOOT button (active low)
    "button_pin": board.BUTTON,
    "button_active_low": True,
}


# ──── SELECT YOUR BOARD ─────────────────────────────────────────
# Uncomment the line matching your hardware:

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


def get_config():
    """Return the active board configuration dict."""
    return ACTIVE_BOARD
