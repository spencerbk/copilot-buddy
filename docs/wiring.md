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

## General Tips

- Always use **3.3V** logic — the ESP32-S3 is not 5V tolerant
- For loose-wire builds, keep SPI wires short (<15 cm) for signal integrity
- Most display modules have on-board level shifting and voltage regulation
- If the display shows garbled output, check the SPI bus frequency (try lowering to 20 MHz)
- If colors look wrong on ST7789, try toggling `color_order` between `"RGB"` and `"BGR"` in config.py
