"""Board adapter configuration for copilot-buddy (MicroPython).

Edit ACTIVE_BOARD below to match your hardware, then save.
Each adapter dict contains all the pin assignments, display parameters,
and bus settings needed to initialize the board.

Pin values are integers for use with machine.Pin().
"""


# ──── Board Adapters ────────────────────────────────────────────

BOARD_M5STICKC_PLUS2 = {
    "name": "M5StickC Plus2",
    "display_type": "ST7789",
    "width": 135,
    "height": 240,
    "rotation": 1,
    # SPI pins
    "sck": 13,
    "mosi": 15,
    "cs": 5,
    "dc": 23,
    "rst": 18,
    "bl": 27,
    "bl_active_high": True,
    "bus_frequency": 40_000_000,
    "color_order": "BGR",
    "colstart": 52,
    "rowstart": 40,
    # Button A (front)
    "button_pin": 37,
    "button_active_low": True,
}

BOARD_LILYGO_T_DISPLAY_S3 = {
    "name": "LILYGO T-Display-S3",
    "display_type": "ST7789",
    "width": 170,
    "height": 320,
    "rotation": 0,
    # SPI pins
    "sck": 12,
    "mosi": 11,
    "cs": 10,
    "dc": 13,
    "rst": 9,
    "bl": 38,
    "bl_active_high": True,
    "bus_frequency": 40_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # Button 1 (left, active low)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_DEVKIT_SSD1306 = {
    "name": "ESP32-S3 DevKit + SSD1306",
    "display_type": "SSD1306",
    "width": 128,
    "height": 64,
    "rotation": 0,
    # I2C pins
    "sda": 13,
    "scl": 14,
    "i2c_addr": 0x3C,
    "bus_frequency": 400_000,
    # No backlight on OLED
    "bl": None,
    "bl_active_high": False,
    "color_order": None,
    "colstart": 0,
    "rowstart": 0,
    # User button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_DEVKIT_ST7789 = {
    "name": "ESP32-S3 DevKit + ST7789",
    "display_type": "ST7789",
    "width": 240,
    "height": 240,
    "rotation": 0,
    # SPI pins
    "sck": 14,
    "mosi": 13,
    "cs": 10,
    "dc": 9,
    "rst": 8,
    "bl": 7,
    "bl_active_high": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # User button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_DEVKIT_ILI9341 = {
    "name": "ESP32-S3 DevKit + ILI9341",
    "display_type": "ILI9341",
    "width": 240,
    "height": 320,
    "rotation": 0,
    # SPI pins
    "sck": 14,
    "mosi": 13,
    "cs": 10,
    "dc": 9,
    "rst": 8,
    "bl": 7,
    "bl_active_high": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # User button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_QTPY_S2_SSD1306 = {
    "name": "QT Py ESP32-S2 + SSD1306",
    "display_type": "SSD1306",
    "width": 128,
    "height": 64,
    "rotation": 0,
    # I2C pins (STEMMA QT connector)
    "sda": 41,
    "scl": 40,
    "i2c_addr": 0x3C,
    "bus_frequency": 400_000,
    # No backlight on OLED
    "bl": None,
    "bl_active_high": False,
    "color_order": None,
    "colstart": 0,
    "rowstart": 0,
    # BOOT button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_QTPY_S2_ST7789 = {
    "name": "QT Py ESP32-S2 + ST7789",
    "display_type": "ST7789",
    "width": 240,
    "height": 240,
    "rotation": 0,
    # SPI pins
    "sck": 36,
    "mosi": 35,
    "cs": 18,       # A0
    "dc": 17,       # A1
    "rst": 9,       # A2
    "bl": 8,        # A3
    "bl_active_high": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # BOOT button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_QTPY_S2_ILI9341 = {
    "name": "QT Py ESP32-S2 + ILI9341",
    "display_type": "ILI9341",
    "width": 240,
    "height": 320,
    "rotation": 0,
    # SPI pins (same as ST7789)
    "sck": 36,
    "mosi": 35,
    "cs": 18,
    "dc": 17,
    "rst": 9,
    "bl": 8,
    "bl_active_high": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # BOOT button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_QTPY_S3_SSD1306 = {
    "name": "QT Py ESP32-S3 + SSD1306",
    "display_type": "SSD1306",
    "width": 128,
    "height": 64,
    "rotation": 0,
    # I2C pins (STEMMA QT connector)
    "sda": 41,
    "scl": 40,
    "i2c_addr": 0x3C,
    "bus_frequency": 400_000,
    # No backlight on OLED
    "bl": None,
    "bl_active_high": False,
    "color_order": None,
    "colstart": 0,
    "rowstart": 0,
    # BOOT button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_QTPY_S3_ST7789 = {
    "name": "QT Py ESP32-S3 + ST7789",
    "display_type": "ST7789",
    "width": 240,
    "height": 240,
    "rotation": 0,
    # SPI pins
    "sck": 36,
    "mosi": 35,
    "cs": 18,       # A0
    "dc": 17,       # A1
    "rst": 9,       # A2
    "bl": 8,        # A3
    "bl_active_high": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # BOOT button (active low with pull-up)
    "button_pin": 0,
    "button_active_low": True,
}

BOARD_QTPY_S3_ILI9341 = {
    "name": "QT Py ESP32-S3 + ILI9341",
    "display_type": "ILI9341",
    "width": 240,
    "height": 320,
    "rotation": 0,
    # SPI pins (same as ST7789)
    "sck": 36,
    "mosi": 35,
    "cs": 18,
    "dc": 17,
    "rst": 9,
    "bl": 8,
    "bl_active_high": True,
    "bus_frequency": 24_000_000,
    "color_order": "BGR",
    "colstart": 0,
    "rowstart": 0,
    # BOOT button (active low with pull-up)
    "button_pin": 0,
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
