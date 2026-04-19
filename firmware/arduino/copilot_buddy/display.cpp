#include "display.h"
#include "config.h"

static uint8_t _textSize = 1;

// ─── Color TFT path (TFT_eSPI) ──────────────────────────────────────────────
#if IS_COLOR_DISPLAY

#include <TFT_eSPI.h>
static TFT_eSPI tft;

void display_init() {
    tft.init();
    tft.setRotation(DISPLAY_ROTATION);
    tft.fillScreen(TFT_BLACK);
    tft.setTextSize(1);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    display_set_backlight(true);
}

void display_clear() {
    tft.fillScreen(TFT_BLACK);
}

void display_text(const char* text, int x, int y, uint16_t color) {
    tft.setTextColor(color, TFT_BLACK);
    int lineH = 8 * _textSize;
    int curY = y;

    while (*text) {
        const char* lineEnd = text;
        while (*lineEnd && *lineEnd != '\n') lineEnd++;
        int len = lineEnd - text;

        if (len > 0) {
            char buf[128];
            if (len > 127) len = 127;
            memcpy(buf, text, len);
            buf[len] = '\0';
            tft.setCursor(x, curY);
            tft.print(buf);
        }

        curY += lineH;
        text = (*lineEnd == '\n') ? lineEnd + 1 : lineEnd;
    }
}

void display_set_text_size(uint8_t size) {
    _textSize = size;
    tft.setTextSize(size);
}

void display_set_backlight(bool on) {
    #if PIN_BL >= 0
    pinMode(PIN_BL, OUTPUT);
    digitalWrite(PIN_BL, (on == BL_ACTIVE_HIGH) ? HIGH : LOW);
    #endif
}

void display_show() {
    // TFT_eSPI renders immediately — no-op
}

int display_width()  { return tft.width(); }
int display_height() { return tft.height(); }

// ─── Monochrome OLED path (Adafruit SSD1306) ────────────────────────────────
#else

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

static Adafruit_SSD1306 oled(DISPLAY_WIDTH, DISPLAY_HEIGHT, &Wire, -1);

void display_init() {
    Wire.begin(PIN_SDA, PIN_SCL);
    if (!oled.begin(SSD1306_SWITCHCAPVCC, I2C_ADDR)) {
        Serial.println(F("SSD1306 init failed"));
        while (true) delay(1000);
    }
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    oled.display();
}

void display_clear() {
    oled.clearDisplay();
}

void display_text(const char* text, int x, int y, uint16_t color) {
    oled.setTextColor(color);
    int lineH = 8 * _textSize;
    int curY = y;

    while (*text) {
        const char* lineEnd = text;
        while (*lineEnd && *lineEnd != '\n') lineEnd++;
        int len = lineEnd - text;

        if (len > 0) {
            char buf[128];
            if (len > 127) len = 127;
            memcpy(buf, text, len);
            buf[len] = '\0';
            oled.setCursor(x, curY);
            oled.print(buf);
        }

        curY += lineH;
        text = (*lineEnd == '\n') ? lineEnd + 1 : lineEnd;
    }
}

void display_set_text_size(uint8_t size) {
    _textSize = size;
    oled.setTextSize(size);
}

void display_set_backlight(bool on) {
    (void)on;   // OLED has no backlight pin
}

void display_show() {
    oled.display();
}

int display_width()  { return DISPLAY_WIDTH; }
int display_height() { return DISPLAY_HEIGHT; }

#endif
