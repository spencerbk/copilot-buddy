"""Display driver abstraction for copilot-buddy (MicroPython).

Factory function ``init_display`` accepts a board config dict and returns
an initialised display object.  Supports ST7789, ILI9341 (SPI/TFT) and
SSD1306 (I2C/OLED).

Required libraries (install via mpremote or copy to /lib):
- st7789_mpy  — for ST7789 displays
- ili9341     — for ILI9341 displays
- ssd1306     — for SSD1306 OLEDs (included in micropython-lib)
"""

from machine import Pin

# Colour TFT display types that have a backlight
_COLOR_TYPES = ("ST7789", "ILI9341")

# Cached backlight Pin object
_bl_pin_obj = None


def is_color_display(config):
    """Return True for colour TFT displays, False for monochrome OLED."""
    return config.get("display_type", "") in _COLOR_TYPES


# ── internal helpers ────────────────────────────────────────────


def _init_st7789(config):
    """Initialise an ST7789 SPI display."""
    try:
        import st7789  # noqa: I001
    except ImportError:
        raise RuntimeError("st7789 lib missing — install st7789_mpy")

    from machine import SPI

    spi = SPI(
        1,
        baudrate=config.get("bus_frequency", 24_000_000),
        sck=Pin(config["sck"]),
        mosi=Pin(config["mosi"]),
    )

    display = st7789.ST7789(
        spi,
        config["width"],
        config["height"],
        cs=Pin(config["cs"], Pin.OUT),
        dc=Pin(config["dc"], Pin.OUT),
        reset=Pin(config["rst"], Pin.OUT) if config.get("rst") else None,
        rotation=config.get("rotation", 0),
    )
    display.init()
    return display


def _init_ili9341(config):
    """Initialise an ILI9341 SPI display."""
    try:
        import ili9341  # noqa: I001
    except ImportError:
        raise RuntimeError("ili9341 lib missing")

    from machine import SPI

    spi = SPI(
        1,
        baudrate=config.get("bus_frequency", 24_000_000),
        sck=Pin(config["sck"]),
        mosi=Pin(config["mosi"]),
    )

    display = ili9341.ILI9341(
        spi,
        cs=Pin(config["cs"], Pin.OUT),
        dc=Pin(config["dc"], Pin.OUT),
        rst=Pin(config["rst"], Pin.OUT) if config.get("rst") else None,
        w=config["width"],
        h=config["height"],
        r=config.get("rotation", 0),
    )
    return display


def _init_ssd1306(config):
    """Initialise an SSD1306 I2C OLED display."""
    try:
        import ssd1306  # noqa: I001
    except ImportError:
        raise RuntimeError("ssd1306 lib missing")

    from machine import I2C

    i2c = I2C(
        0,
        scl=Pin(config["scl"]),
        sda=Pin(config["sda"]),
        freq=config.get("bus_frequency", 400_000),
    )

    display = ssd1306.SSD1306_I2C(
        config["width"],
        config["height"],
        i2c,
        addr=config.get("i2c_addr", 0x3C),
    )
    return display


# Map config string → initialiser
_DRIVERS = {
    "ST7789": _init_st7789,
    "ILI9341": _init_ili9341,
    "SSD1306": _init_ssd1306,
}


# ── public API ──────────────────────────────────────────────────


def init_display(config):
    """Initialise and return a display from *config*."""
    display_type = config.get("display_type", "")
    init_fn = _DRIVERS.get(display_type)
    if init_fn is None:
        raise ValueError("Unknown display_type: " + display_type)

    try:
        display = init_fn(config)
    except RuntimeError as exc:
        print("Display init failed:", exc)
        raise

    # Turn on the backlight for TFT boards
    if is_color_display(config):
        set_backlight(config, True)

    return display


def set_backlight(config, on):
    """Turn the backlight on or off.

    Respects ``bl_active_high`` to handle active-low backlight circuits.
    No-op for OLED displays which have no backlight pin.
    """
    global _bl_pin_obj  # noqa: PLW0603

    if not is_color_display(config):
        return

    bl_pin = config.get("bl")
    if bl_pin is None:
        return

    active_high = config.get("bl_active_high", True)
    value = on if active_high else (not on)

    if _bl_pin_obj is None:
        _bl_pin_obj = Pin(bl_pin, Pin.OUT)

    _bl_pin_obj.value(1 if value else 0)
