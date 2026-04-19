#pragma once

// ============================================================================
// copilot-buddy — Board Configuration
//
// Uncomment ONE board preset below, or pass -DBOARD_xxx via build_flags.
// Pin assignments match the CircuitPython reference (firmware/circuitpython/config.py).
// ============================================================================

// Uncomment ONE board preset (or define via platformio.ini build_flags):
// #define BOARD_M5STICKC_PLUS2
// #define BOARD_LILYGO_T_DISPLAY_S3
// #define BOARD_DEVKIT_SSD1306
// #define BOARD_DEVKIT_ST7789
// #define BOARD_DEVKIT_ILI9341

// Default to DEVKIT_ST7789 if nothing is defined
#if !defined(BOARD_M5STICKC_PLUS2) && !defined(BOARD_LILYGO_T_DISPLAY_S3) && \
    !defined(BOARD_DEVKIT_SSD1306) && !defined(BOARD_DEVKIT_ST7789) && \
    !defined(BOARD_DEVKIT_ILI9341)
  #define BOARD_DEVKIT_ST7789
#endif

// ─── M5StickC Plus2 ─────────────────────────────────────────────────────────
#if defined(BOARD_M5STICKC_PLUS2)
  #define BOARD_NAME        "M5StickC Plus2"
  #define DISPLAY_TYPE      "ST7789"
  #define DISPLAY_WIDTH     135
  #define DISPLAY_HEIGHT    240
  #define DISPLAY_ROTATION  1
  #define PIN_SCK           13
  #define PIN_MOSI          15
  #define PIN_CS            5
  #define PIN_DC            23
  #define PIN_RST           18
  #define PIN_BL            27
  #define BL_ACTIVE_HIGH    true
  #define SPI_FREQ          40000000
  #define TFT_COLOR_ORDER   1       // BGR
  #define TFT_COLSTART      52
  #define TFT_ROWSTART      40
  #define PIN_BUTTON        37
  #define BUTTON_ACTIVE_LOW true
  #define IS_COLOR_DISPLAY  true
  #define IS_SPI_DISPLAY    true

// ─── LILYGO T-Display-S3 ────────────────────────────────────────────────────
#elif defined(BOARD_LILYGO_T_DISPLAY_S3)
  #define BOARD_NAME        "LILYGO T-Display-S3"
  #define DISPLAY_TYPE      "ST7789"
  #define DISPLAY_WIDTH     170
  #define DISPLAY_HEIGHT    320
  #define DISPLAY_ROTATION  0
  #define PIN_SCK           12
  #define PIN_MOSI          11
  #define PIN_CS            10
  #define PIN_DC            13
  #define PIN_RST           9
  #define PIN_BL            38
  #define BL_ACTIVE_HIGH    true
  #define SPI_FREQ          40000000
  #define TFT_COLOR_ORDER   1       // BGR
  #define TFT_COLSTART      0
  #define TFT_ROWSTART      0
  #define PIN_BUTTON        0
  #define BUTTON_ACTIVE_LOW true
  #define IS_COLOR_DISPLAY  true
  #define IS_SPI_DISPLAY    true

// ─── ESP32-S3 DevKit + SSD1306 I2C OLED ─────────────────────────────────────
#elif defined(BOARD_DEVKIT_SSD1306)
  #define BOARD_NAME        "ESP32-S3 DevKit + SSD1306"
  #define DISPLAY_TYPE      "SSD1306"
  #define DISPLAY_WIDTH     128
  #define DISPLAY_HEIGHT    64
  #define DISPLAY_ROTATION  0
  #define PIN_SDA           13
  #define PIN_SCL           14
  #define I2C_ADDR          0x3C
  #define PIN_BL            -1
  #define BL_ACTIVE_HIGH    false
  #define PIN_BUTTON        0
  #define BUTTON_ACTIVE_LOW true
  #define IS_COLOR_DISPLAY  false
  #define IS_SPI_DISPLAY    false

// ─── ESP32-S3 DevKit + ST7789 SPI TFT (default) ─────────────────────────────
#elif defined(BOARD_DEVKIT_ST7789)
  #define BOARD_NAME        "ESP32-S3 DevKit + ST7789"
  #define DISPLAY_TYPE      "ST7789"
  #define DISPLAY_WIDTH     240
  #define DISPLAY_HEIGHT    240
  #define DISPLAY_ROTATION  0
  #define PIN_SCK           14
  #define PIN_MOSI          13
  #define PIN_CS            10
  #define PIN_DC            9
  #define PIN_RST           8
  #define PIN_BL            7
  #define BL_ACTIVE_HIGH    true
  #define SPI_FREQ          24000000
  #define TFT_COLOR_ORDER   1       // BGR
  #define TFT_COLSTART      0
  #define TFT_ROWSTART      0
  #define PIN_BUTTON        0
  #define BUTTON_ACTIVE_LOW true
  #define IS_COLOR_DISPLAY  true
  #define IS_SPI_DISPLAY    true

// ─── ESP32-S3 DevKit + ILI9341 SPI TFT ──────────────────────────────────────
#elif defined(BOARD_DEVKIT_ILI9341)
  #define BOARD_NAME        "ESP32-S3 DevKit + ILI9341"
  #define DISPLAY_TYPE      "ILI9341"
  #define DISPLAY_WIDTH     240
  #define DISPLAY_HEIGHT    320
  #define DISPLAY_ROTATION  0
  #define PIN_SCK           14
  #define PIN_MOSI          13
  #define PIN_CS            10
  #define PIN_DC            9
  #define PIN_RST           8
  #define PIN_BL            7
  #define BL_ACTIVE_HIGH    true
  #define SPI_FREQ          24000000
  #define TFT_COLOR_ORDER   1       // BGR
  #define TFT_COLSTART      0
  #define TFT_ROWSTART      0
  #define PIN_BUTTON        0
  #define BUTTON_ACTIVE_LOW true
  #define IS_COLOR_DISPLAY  true
  #define IS_SPI_DISPLAY    true

#else
  #error "No board preset defined. Uncomment one in config.h or pass -DBOARD_xxx."
#endif

// ─── Disconnect thresholds (ms) ─────────────────────────────────────────────
#define DISCONNECT_WARN_MS   10000
#define DISCONNECT_SLEEP_MS  300000
