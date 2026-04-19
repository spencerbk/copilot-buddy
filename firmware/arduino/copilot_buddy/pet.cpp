#include "pet.h"
#include "display.h"
#include <pgmspace.h>

// ─── Constructor ─────────────────────────────────────────────────────────────

PetAnimator::PetAnimator(const PetFrames* pet, int fps)
    : _pet(pet)
    , _currentState(STATE_IDLE)
    , _frameIndex(0)
    , _lastFrameMs(0)
    , _frameInterval(1000 / fps)
{
}

// ─── State management ────────────────────────────────────────────────────────

void PetAnimator::setState(PetState state) {
    if (state != _currentState) {
        _currentState = state;
        _frameIndex = 0;
        // Render immediately on state change
        int count = 0;
        const char* const* frames = getFrames(_currentState, count);
        if (count > 0) {
            const char* frame = (const char*)pgm_read_ptr(&frames[0]);
            renderFrame(frame, "");
        }
    }
}

// ─── Animation tick ──────────────────────────────────────────────────────────

void PetAnimator::update(unsigned long now_ms, const char* statusText) {
    if (now_ms - _lastFrameMs < (unsigned long)_frameInterval) return;

    int count = 0;
    const char* const* frames = getFrames(_currentState, count);
    if (count > 0) {
        _frameIndex = (_frameIndex + 1) % count;
        const char* frame = (const char*)pgm_read_ptr(&frames[_frameIndex]);
        renderFrame(frame, statusText);
    }
    _lastFrameMs = now_ms;
}

// ─── Frame lookup ────────────────────────────────────────────────────────────

const char* const* PetAnimator::getFrames(PetState s, int& count) {
    switch (s) {
        case STATE_SLEEP:     count = _pet->sleepCount;     return _pet->sleep;
        case STATE_IDLE:      count = _pet->idleCount;      return _pet->idle;
        case STATE_BUSY:      count = _pet->busyCount;      return _pet->busy;
        case STATE_ATTENTION: count = _pet->attentionCount;  return _pet->attention;
        case STATE_CELEBRATE: count = _pet->celebrateCount;  return _pet->celebrate;
        case STATE_DIZZY:     count = _pet->dizzyCount;      return _pet->dizzy;
        case STATE_HEART:     count = _pet->heartCount;      return _pet->heart;
        default:              count = _pet->idleCount;       return _pet->idle;
    }
}

// ─── Rendering ───────────────────────────────────────────────────────────────

void PetAnimator::renderFrame(const char* frame, const char* status) {
    display_clear();

    int w = display_width();
    int h = display_height();

    // Choose text size based on display height
    uint8_t textSize = (h >= 200) ? 2 : 1;
    display_set_text_size(textSize);

    int charW = 6 * textSize;
    int charH = 8 * textSize;

    // Estimate art block size (typical pet art: ~14 chars wide, 4 lines)
    int artW = 14 * charW;
    int artH = 4 * charH;

    // Center horizontally
    int artX = (w - artW) / 2;
    if (artX < 2) artX = 2;

    // Vertically: center in area above the status line
    int statusReserve = charH + 4;
    int availH = h - statusReserve;
    int artY = (availH - artH) / 2;
    if (artY < 2) artY = 2;

    display_text(frame, artX, artY);

    // Status text at bottom
    if (status && status[0]) {
        int statusY = h - charH - 2;
        display_text(status, artX, statusY);
    }

    display_show();
}
