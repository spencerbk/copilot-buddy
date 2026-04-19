// copilot-buddy — ESP32-S3 desk pet for GitHub Copilot CLI (Arduino/PlatformIO)
//
// Reads JSON events from the host bridge over USB serial, maps them to
// pet animation states, and renders the active pet on the display.

#include "config.h"
#include "display.h"
#include "state.h"
#include "pet.h"
#include "buddies/octocat.h"
#include <ArduinoJson.h>

// ─── Globals ─────────────────────────────────────────────────────────────────

StateManager stateManager;
PetAnimator  animator(&OCTOCAT_PET);

// Non-blocking serial line buffer
static char serialBuf[512];
static int  serialPos = 0;

// ─── Status command response ─────────────────────────────────────────────────

static void handleStatusCmd() {
    JsonDocument doc;
    doc["ack"] = "status";
    doc["ok"]  = true;
    JsonObject data = doc["data"].to<JsonObject>();
    data["pet"]       = "octocat";
    data["uptime"]    = millis() / 1000;
    data["heap_free"] = (unsigned long)ESP.getFreeHeap();
    data["display"]   = DISPLAY_TYPE;

    serializeJson(doc, Serial);
    Serial.println();
}

// ─── Serial processing ──────────────────────────────────────────────────────

static void processSerialLine(const char* line, unsigned long now) {
    // Check for device-level commands before passing to state manager
    if (strstr(line, "\"cmd\"") && strstr(line, "\"status\"")) {
        handleStatusCmd();
        return;
    }
    stateManager.processMessage(line, now);
}

static void readSerial(unsigned long now) {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n') {
            serialBuf[serialPos] = '\0';
            if (serialPos > 0) {
                processSerialLine(serialBuf, now);
            }
            serialPos = 0;
        } else if (c != '\r' && serialPos < (int)sizeof(serialBuf) - 1) {
            serialBuf[serialPos++] = c;
        }
        // Bytes beyond buffer capacity are silently dropped (prevents OOM)
    }
}

// ─── Arduino entry points ────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    Serial.println(F("copilot-buddy: starting..."));

    display_init();
    animator.setState(STATE_IDLE);

    Serial.println(F("copilot-buddy: ready"));
}

void loop() {
    unsigned long now = millis();

    // 1. Read serial (non-blocking)
    readSerial(now);

    // 2. Tick state machine (timed expiry, disconnect check)
    PetState cur = stateManager.update(now);
    animator.setState(cur);

    // 3. Build status text
    char statusBuf[32] = "";
    if (stateManager.state == STATE_BUSY && stateManager.query[0]) {
        snprintf(statusBuf, sizeof(statusBuf), "%.20s", stateManager.query);
    } else if (stateManager.disconnected) {
        strncpy(statusBuf, "~ disconnected ~", sizeof(statusBuf) - 1);
        statusBuf[sizeof(statusBuf) - 1] = '\0';
    } else if (stateManager.queriesToday > 0) {
        snprintf(statusBuf, sizeof(statusBuf), "q:%d", stateManager.queriesToday);
    }

    // 4. Advance animation frame
    animator.update(now, statusBuf);

    delay(50);  // ~20 Hz
}
