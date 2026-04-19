#include "state.h"
#include "config.h"
#include <ArduinoJson.h>
#include <string.h>

// Hold durations for timed states (ms)
static const unsigned long HOLD_ATTENTION = 3000;
static const unsigned long HOLD_CELEBRATE = 5000;
static const unsigned long HOLD_DIZZY     = 3000;
static const unsigned long HOLD_HEART     = 2000;

// Priority lookup — higher number wins
static int statePriority(PetState s) {
    switch (s) {
        case STATE_SLEEP:     return 1;
        case STATE_IDLE:      return 2;
        case STATE_BUSY:      return 3;
        case STATE_ATTENTION: return 4;
        case STATE_HEART:     return 5;
        case STATE_CELEBRATE: return 6;
        case STATE_DIZZY:     return 7;
        default:              return 0;
    }
}

static unsigned long holdDuration(PetState s) {
    switch (s) {
        case STATE_ATTENTION: return HOLD_ATTENTION;
        case STATE_HEART:     return HOLD_HEART;
        case STATE_CELEBRATE: return HOLD_CELEBRATE;
        case STATE_DIZZY:     return HOLD_DIZZY;
        default:              return 3000;
    }
}

// ─── Constructor ─────────────────────────────────────────────────────────────

StateManager::StateManager()
    : state(STATE_SLEEP)
    , baseState(STATE_SLEEP)
    , query(_queryBuf)
    , queriesToday(0)
    , totalQueries(0)
    , disconnected(false)
    , timedState(STATE_IDLE)
    , _hasTimedState(false)
    , timedUntil(0)
    , lastHeartbeat(0)
    , lastStartTime(0)
{
    _queryBuf[0] = '\0';
}

// ─── Public API ──────────────────────────────────────────────────────────────

PetState StateManager::processMessage(const char* json, unsigned long now_ms) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, json);
    if (err) return state;

    const char* evt      = doc["evt"];
    const char* stateStr = doc["state"];

    if (evt) {
        handleEvent(evt, now_ms);
    } else if (stateStr) {
        // Update metadata from heartbeat
        const char* q = doc["query"];
        if (q) {
            strncpy(_queryBuf, q, sizeof(_queryBuf) - 1);
            _queryBuf[sizeof(_queryBuf) - 1] = '\0';
        }
        queriesToday = doc["queries_today"] | queriesToday;
        totalQueries = doc["total_queries"] | totalQueries;

        handleHeartbeat(stateStr, now_ms);
    }

    return resolve(now_ms);
}

PetState StateManager::update(unsigned long now_ms) {
    return resolve(now_ms);
}

// ─── Event handling ──────────────────────────────────────────────────────────

void StateManager::handleEvent(const char* evt, unsigned long now_ms) {
    if (strcmp(evt, "start") == 0) {
        lastStartTime = now_ms;
        baseState = STATE_BUSY;
    } else if (strcmp(evt, "end") == 0) {
        unsigned long duration = now_ms - lastStartTime;
        if (duration < 3000) {
            setTimedState(STATE_HEART, now_ms);
        } else {
            setTimedState(STATE_ATTENTION, now_ms);
        }
        baseState = STATE_IDLE;
    } else if (strcmp(evt, "error") == 0) {
        setTimedState(STATE_DIZZY, now_ms);
    } else if (strcmp(evt, "milestone") == 0) {
        setTimedState(STATE_CELEBRATE, now_ms);
    }
}

void StateManager::handleHeartbeat(const char* stateStr, unsigned long now_ms) {
    lastHeartbeat = now_ms;
    disconnected = false;

    if (strcmp(stateStr, "error") == 0) {
        setTimedState(STATE_DIZZY, now_ms);
    } else if (strcmp(stateStr, "busy") == 0) {
        baseState = STATE_BUSY;
    } else if (strcmp(stateStr, "sleep") == 0) {
        baseState = STATE_SLEEP;
    } else {
        baseState = STATE_IDLE;
    }
}

// ─── Timed-state logic ──────────────────────────────────────────────────────

void StateManager::setTimedState(PetState s, unsigned long now_ms) {
    unsigned long duration = holdDuration(s);
    if (_hasTimedState) {
        int curPri = statePriority(timedState);
        int newPri = statePriority(s);
        if (newPri < curPri && now_ms < timedUntil) {
            return;  // current timed state has higher priority
        }
    }
    timedState = s;
    timedUntil = now_ms + duration;
    _hasTimedState = true;
}

PetState StateManager::resolve(unsigned long now_ms) {
    // Expire timed state
    if (_hasTimedState && now_ms >= timedUntil) {
        _hasTimedState = false;
    }

    // Disconnect detection (only after first heartbeat)
    if (lastHeartbeat > 0) {
        unsigned long gap = now_ms - lastHeartbeat;
        if (gap >= DISCONNECT_SLEEP_MS) {
            baseState = STATE_SLEEP;
            disconnected = true;
        } else if (gap >= DISCONNECT_WARN_MS) {
            baseState = STATE_IDLE;
            disconnected = true;
        } else {
            disconnected = false;
        }
    }

    // Pick highest-priority active state
    if (_hasTimedState) {
        int tsPri = statePriority(timedState);
        int bsPri = statePriority(baseState);
        state = (tsPri >= bsPri) ? timedState : baseState;
    } else {
        state = baseState;
    }

    return state;
}
