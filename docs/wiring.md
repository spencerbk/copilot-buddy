# Wiring Guide

Pin diagrams for each supported board/display combination.

---

## ESP32-S3 DevKit + ST7789 (240×240 TFT) — Default

```
ESP32-S3 DevKit          ST7789 TFT Module
─────────────           ─────────────────
  GPIO 14 (SCK)  ──────  SCK / CLK
  GPIO 13 (MOSI) ──────  SDA / MOSI
  GPIO 10        ──────  CS
  GPIO  9        ──────  DC
  GPIO  8        ──────  RST
  GPIO  7        ──────  BL (Backlight)
  3.3V           ──────  VCC
  GND            ──────  GND

  GPIO  0        ──────  Button (to GND, internal pull-up)
```

**Notes:** SPI bus at 40 MHz. Backlight is active-high. Button uses internal pull-up (press = LOW).

---

## ESP32-S3 DevKit + SSD1306 (128×64 OLED)

```
ESP32-S3 DevKit          SSD1306 OLED Module
─────────────           ──────────────────
  GPIO 14 (SCL)  ──────  SCL / SCK
  GPIO 13 (SDA)  ──────  SDA
  3.3V           ──────  VCC
  GND            ──────  GND

  GPIO  0        ──────  Button (to GND, internal pull-up)
```

**Notes:** I2C address `0x3C` (default for most SSD1306 modules). No backlight pin — OLED is self-emitting. Bus speed 400 kHz.

---

## ESP32-S3 DevKit + ILI9341 (240×320 TFT)

```
ESP32-S3 DevKit          ILI9341 TFT Module
─────────────           ─────────────────
  GPIO 14 (SCK)  ──────  SCK / CLK
  GPIO 13 (MOSI) ──────  SDI / MOSI
  GPIO 10        ──────  CS
  GPIO  9        ──────  DC
  GPIO  8        ──────  RST
  GPIO  7        ──────  LED (Backlight)
  3.3V           ──────  VCC
  GND            ──────  GND

  GPIO  0        ──────  Button (to GND, internal pull-up)
```

**Notes:** Same SPI pins as ST7789. ILI9341 modules often have an SD card slot — leave SD pins unconnected. Backlight active-high.

---

## M5StickC Plus2

The M5StickC Plus2 has a **built-in 135×240 ST7789 TFT** — no wiring needed for the display.

```
Internal connections (no user wiring):
  GPIO 13  →  SCK
  GPIO 15  →  MOSI
  GPIO  5  →  CS
  GPIO 23  →  DC
  GPIO 18  →  RST
  GPIO 27  →  Backlight (PWM)

Buttons:
  GPIO 37  →  Button A (front face)
  GPIO 39  →  Button B (side)
```

**Notes:** Display uses BGR color order with `colstart=52, rowstart=40` offset. Backlight supports PWM dimming.

---

## LILYGO T-Display-S3

The T-Display-S3 has a **built-in 170×320 ST7789 TFT** — no wiring needed for the display.

```
Internal connections (no user wiring):
  GPIO 12  →  SCK
  GPIO 11  →  MOSI
  GPIO 10  →  CS
  GPIO 13  →  DC
  GPIO  9  →  RST
  GPIO 38  →  Backlight

Buttons:
  GPIO  0  →  Button 1 (BOOT)
  GPIO 14  →  Button 2
```

**Notes:** Display uses RGB color order. Power pin GPIO 15 may need to be set HIGH to enable the display on some board revisions.

---

## Adafruit QT Py ESP32-S2 / ESP32-S3 + SSD1306 (128×64 OLED)

Both QT Py boards use the **STEMMA QT / Qwiic connector** for I2C — just plug in an SSD1306 OLED breakout. No wiring needed!

```
QT Py (S2 or S3)           SSD1306 OLED (STEMMA QT)
─────────────────          ────────────────────────
  STEMMA QT SDA1   ──────  SDA    (GPIO 41)
  STEMMA QT SCL1   ──────  SCL    (GPIO 40)
  3.3V              ──────  VCC
  GND               ──────  GND

  BOOT button       ──────  GPIO 0 (built-in, active low)
```

**Notes:** Plug a STEMMA QT / Qwiic cable directly between the QT Py and an SSD1306 breakout with a STEMMA QT connector (e.g., Adafruit #4440 or #5649). I2C address `0x3C`. No soldering required.

---

## Adafruit QT Py ESP32-S2 / ESP32-S3 + ST7789 (240×240 TFT)

SPI TFT wiring — uses the QT Py's analog/digital header pins for display control.

```
QT Py (S2 or S3)           ST7789 TFT Module
─────────────────          ─────────────────
  GPIO 36 (SCK)     ──────  SCK / CLK
  GPIO 35 (MOSI)    ──────  SDA / MOSI
  GPIO 18 (A0)      ──────  CS
  GPIO 17 (A1)      ──────  DC
  GPIO  9 (A2)      ──────  RST
  GPIO  8 (A3)      ──────  BL (Backlight)
  3.3V               ──────  VCC
  GND                ──────  GND

  BOOT button        ──────  GPIO 0 (built-in, active low)
```

**Notes:** This wiring uses 6 of the 8 available header pins. Keep SPI wires short. Backlight is active-high. SPI bus at 24 MHz.

---

## Adafruit QT Py ESP32-S2 / ESP32-S3 + ILI9341 (240×320 TFT)

SPI TFT wiring — same pins as ST7789. Compatible with the Adafruit 2.8" TFT breakout (#2090).

```
QT Py (S2 or S3)           ILI9341 TFT Module
─────────────────          ─────────────────
  GPIO 36 (SCK)     ──────  SCK / CLK
  GPIO 35 (MOSI)    ──────  SDI / MOSI
  GPIO 18 (A0)      ──────  CS
  GPIO 17 (A1)      ──────  DC
  GPIO  9 (A2)      ──────  RST
  GPIO  8 (A3)      ──────  LED (Backlight)
  3.3V               ──────  VCC
  GND                ──────  GND

  BOOT button        ──────  GPIO 0 (built-in, active low)
```

**Notes:** Same SPI pins as ST7789. ILI9341 modules with an SD card slot — leave SD pins unconnected. Backlight active-high. If using the Adafruit 2.8" capacitive touch breakout (#2090), the touch I2C pins can use the STEMMA QT connector.

---

## Adafruit QT Py ESP32-S2 / ESP32-S3 + EYESPI BFF + ILI9341 (240×320 TFT)

Uses the Adafruit EYESPI BFF breakout with an 18-pin FPC cable to an EYESPI-compatible ILI9341 display. No loose wires for the SPI bus — CS and DC are routed through the BFF. Use board config `_qtpy_s2_eyespi_ili9341()` in config.py.

```
QT Py (S2 or S3)           EYESPI BFF           ILI9341 Display
─────────────────          ──────────           ───────────────
  SCK  (SPI default) ──────  SCK      ─── FPC ──  SCK / CLK
  MOSI (SPI default) ──────  MOSI     ─── FPC ──  SDI / MOSI
  TX                 ──────  TFT CS   ─── FPC ──  CS
  RX                 ──────  TFT DC   ─── FPC ──  DC
  (not connected)            RST      ─── FPC ──  RST  (solder pad on BFF)
  (not connected)            LITE     ─── FPC ──  LED  (solder pad on BFF, default-on)
  SDA / SCL (I2C)    ──────  SDA/SCL  ─── FPC ──  Touch I2C (if present)
  3.3V               ──────  3V       ─── FPC ──  VCC
  GND                ──────  GND      ─── FPC ──  GND

  BOOT button        ──────  GPIO 0 (built-in, active low)
```

**Notes:** RST and backlight are exposed as through-hole solder pads on the BFF but are **not connected to any QT Py pin by default**. The ILI9341 breakout's backlight is on by default so no control pin is needed. If your display requires reset control, solder a jumper wire from the RST pad to a free GPIO and update config.py. Touch I2C (FT6206 at address 0x38) is routed through the **QT Py header I2C** (SDA/SCL) via the EYESPI BFF's FPC connector — not the STEMMA QT port. On the QT Py ESP32-S2/S3, header I2C and STEMMA QT are separate buses. Install `adafruit_focaltouch` and `adafruit_bus_device` from the Adafruit Bundle. The `touch_input.py` driver is loaded automatically when `touch_i2c_addr` is set in the board config.

---

## General Tips

- Always use **3.3V** logic — the ESP32-S2 and ESP32-S3 are not 5V tolerant
- For loose-wire builds, keep SPI wires short (<15 cm) for signal integrity
- Most display modules have on-board level shifting and voltage regulation
- If the display shows garbled output, check the SPI bus frequency (try lowering to 20 MHz)
- If colors look wrong on ST7789, try toggling `color_order` between `"RGB"` and `"BGR"` in config.py
