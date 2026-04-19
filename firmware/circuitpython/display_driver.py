"""Display driver abstraction for copilot-buddy.

Factory function ``init_display`` accepts a board config dict and returns
an initialised displayio-compatible display object.  Supports ST7789,
ILI9341 (SPI/TFT) and SSD1306 (I2C/OLED).
"""

import busio
import digitalio
import displayio

# --- colour TFT display types that have a backlight ---
_COLOR_TYPES = ("ST7789", "ILI9341")

# Cached backlight pin to avoid re-initializing on each set_backlight() call
_bl_pin_obj = None


def is_color_display(config):
    """Return True for colour TFT displays, False for monochrome OLED."""
    return config.get("display_type", "") in _COLOR_TYPES


# ── internal helpers ────────────────────────────────────────────────


def _init_spi_display(config, driver_cls):
    """Create an SPI-attached TFT display using *driver_cls*."""
    spi = busio.SPI(clock=config["sck"], MOSI=config["mosi"])

    # CircuitPython 9.x: FourWire lives in its own top-level module
    import fourwire  # noqa: E402

    bus = fourwire.FourWire(
        spi,
        command=config["dc"],
        chip_select=config["cs"],
        reset=config.get("rst"),
        baudrate=config.get("bus_frequency", 24_000_000),
    )

    display = driver_cls(
        bus,
        width=config["width"],
        height=config["height"],
        rotation=config.get("rotation", 0),
        colstart=config.get("colstart", 0),
        rowstart=config.get("rowstart", 0),
    )
    return display


def _init_st7789(config):
    try:
        import adafruit_st7789
    except ImportError:
        raise RuntimeError("adafruit_st7789 lib missing")
    return _init_spi_display(config, adafruit_st7789.ST7789)


def _init_ili9341(config):
    try:
        import adafruit_ili9341
    except ImportError:
        raise RuntimeError("adafruit_ili9341 lib missing")
    return _init_spi_display(config, adafruit_ili9341.ILI9341)


def _init_ssd1306(config):
    try:
        import adafruit_ssd1306
    except ImportError:
        raise RuntimeError("adafruit_ssd1306 lib missing")

    # CircuitPython 9.x: I2CDisplayBus is a top-level module
    import i2cdisplaybus

    i2c = busio.I2C(scl=config["scl"], sda=config["sda"])
    bus = i2cdisplaybus.I2CDisplayBus(
        i2c, device_address=config.get("i2c_addr", 0x3C)
    )
    display = adafruit_ssd1306.SSD1306(
        bus,
        width=config["width"],
        height=config["height"],
    )
    return display


# map config string → initialiser
_DRIVERS = {
    "ST7789": _init_st7789,
    "ILI9341": _init_ili9341,
    "SSD1306": _init_ssd1306,
}


# ── public API ──────────────────────────────────────────────────────


def init_display(config):
    """Initialise and return a display from *config*.

    Releases any previously-held displayio buses first to avoid
    "display already in use" errors on soft-reload.
    """
    displayio.release_displays()

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
        return  # OLEDs have no backlight

    bl_pin = config.get("bl")
    if bl_pin is None:
        return

    active_high = config.get("bl_active_high", True)
    value = on if active_high else (not on)

    if _bl_pin_obj is None:
        _bl_pin_obj = digitalio.DigitalInOut(bl_pin)
        _bl_pin_obj.direction = digitalio.Direction.OUTPUT

    _bl_pin_obj.value = value
