#pragma once
#include <Arduino.h>

enum PetState {
    STATE_SLEEP = 0,
    STATE_IDLE,
    STATE_BUSY,
    STATE_ATTENTION,
    STATE_HEART,
    STATE_CELEBRATE,
    STATE_DIZZY
};

class StateManager {
public:
    StateManager();
    PetState processMessage(const char* json, unsigned long now_ms);
    PetState update(unsigned long now_ms);

    PetState state;
    PetState baseState;
    const char* query;
    int queriesToday;
    int totalQueries;
    bool disconnected;

private:
    void handleEvent(const char* evt, unsigned long now_ms);
    void handleHeartbeat(const char* stateStr, unsigned long now_ms);
    void setTimedState(PetState s, unsigned long now_ms);
    PetState resolve(unsigned long now_ms);

    PetState timedState;
    bool _hasTimedState;
    unsigned long timedUntil;
    unsigned long lastHeartbeat;
    unsigned long lastStartTime;
    char _queryBuf[64];
};
