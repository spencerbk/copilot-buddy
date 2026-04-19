#pragma once
#include <Arduino.h>
#include "state.h"

struct PetFrames {
    const char* name;
    const char* const* sleep;      int sleepCount;
    const char* const* idle;       int idleCount;
    const char* const* busy;       int busyCount;
    const char* const* attention;  int attentionCount;
    const char* const* celebrate;  int celebrateCount;
    const char* const* dizzy;      int dizzyCount;
    const char* const* heart;      int heartCount;
};

class PetAnimator {
public:
    PetAnimator(const PetFrames* pet, int fps = 2);
    void setState(PetState state);
    void update(unsigned long now_ms, const char* statusText = "");

private:
    const PetFrames* _pet;
    PetState _currentState;
    int _frameIndex;
    unsigned long _lastFrameMs;
    int _frameInterval;

    const char* const* getFrames(PetState s, int& count);
    void renderFrame(const char* frame, const char* status);
};
