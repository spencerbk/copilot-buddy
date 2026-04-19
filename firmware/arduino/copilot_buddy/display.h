#pragma once
#include <Arduino.h>

void display_init();
void display_clear();
void display_text(const char* text, int x, int y, uint16_t color = 0xFFFF);
void display_set_text_size(uint8_t size);
void display_set_backlight(bool on);
void display_show();
int display_width();
int display_height();
