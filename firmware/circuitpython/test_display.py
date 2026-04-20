"""Minimal display test for QT Py ESP32-S2 + EYESPI BFF + ILI9341.

Run this directly on the device via REPL to verify SPI + display wiring.
If you see a blue screen with white text, the hardware is working.
"""

import board
import busio
import displayio
import terminalio
from adafruit_display_text import label

# Release any previous display
displayio.release_displays()

# EYESPI BFF pin mapping
spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)

import fourwire  # noqa: E402

bus = fourwire.FourWire(
    spi,
    command=board.RX,       # DC pin (EYESPI BFF routes to RX)
    chip_select=board.TX,   # CS pin (EYESPI BFF routes to TX)
    reset=None,             # Not connected on BFF
    baudrate=24_000_000,
)

import adafruit_ili9341  # noqa: E402

display = adafruit_ili9341.ILI9341(bus, width=240, height=320, rotation=0)

# Draw a blue background with white text
splash = displayio.Group()

# Background: solid blue
bg_bitmap = displayio.Bitmap(240, 320, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0x0000FF  # blue
splash.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

# Text
txt = label.Label(terminalio.FONT, text="EYESPI BFF OK!", color=0xFFFFFF, x=60, y=160)
splash.append(txt)

display.root_group = splash

print("Display test complete — you should see blue screen with white text.")
print("If screen is still white, check wiring (CS=TX, DC=RX).")
