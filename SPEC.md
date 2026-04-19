# copilot-buddy — Implementation Spec

## Overview

An ESP32-S2/S3-based desk pet that connects to your computer and reacts to
GitHub Copilot CLI activity in real time. Displays an
animated character on an attached TFT/OLED screen that sleeps when idle,
works when a query is in-flight, celebrates on completion, and more.

Inspired by [claude-desktop-buddy](https://github.com/anthropics/claude-desktop-buddy)
by Anthropic (MIT licensed).

---

## Hardware

### Supported Boards (pick one)

| Board                          | Display        | Notes                           |
| ------------------------------ | -------------- | ------------------------------- |
| **M5StickC Plus2**             | 135×240 TFT    | Closest to original project     |
| **LILYGO T-Display-S3**       | 170×320 TFT    | Larger screen, USB-C            |
| **ESP32-S3 DevKit + SSD1306** | 128×64 OLED    | Cheapest, ASCII-only            |
| **ESP32-S3 DevKit + ST7789**  | 240×240 TFT    | Good balance of size and color  |
| **ESP32-S3 DevKit + ILI9341** | 240×320 TFT    | Largest, supports GIF pets      |
| **QT Py ESP32-S2 + SSD1306** | 128×64 OLED    | STEMMA QT, no BLE               |
| **QT Py ESP32-S2 + ST7789**  | 240×240 TFT    | Tiny board, SPI wiring, no BLE  |
| **QT Py ESP32-S2 + ILI9341** | 240×320 TFT    | Tiny board, SPI wiring, no BLE  |
| **QT Py ESP32-S3 + SSD1306** | 128×64 OLED    | STEMMA QT plug-and-play         |
| **QT Py ESP32-S3 + ST7789**  | 240×240 TFT    | Tiny board, SPI wiring          |
| **QT Py ESP32-S3 + ILI9341** | 240×320 TFT    | Tiny board, SPI wiring          |

### Pin Defaults (generic wiring, configurable)

```
TFT/OLED SDA  → GPIO 13
TFT/OLED SCL  → GPIO 14
TFT CS         → GPIO 10
TFT DC         → GPIO 9
TFT RST        → GPIO 8
TFT BL         → GPIO 7
```

> Board-specific pin mappings live in `config.py` (Python) or
> `config.h` (Arduino) and are the first thing the user edits.

---

## Communication Architecture

Since the Copilot CLI has no built-in hardware bridge, we provide a small
**host-side bridge script** that monitors Copilot CLI activity and sends
JSON events to the ESP32 over **USB serial** or **BLE**.

```
┌──────────────────┐        USB/BLE         ┌──────────────────┐
│   Your Computer  │  ───────────────────▶  │  ESP32-S2/S3     │
│                  │    JSON messages        │                  │
│  ┌────────────┐  │    (newline-delim)      │  ┌────────────┐  │
│  │Copilot CLI │  │                        │  │  Display    │  │
│  └─────┬──────┘  │                        │  │  + Pet      │  │
│        │         │                        │  └────────────┘  │
│  ┌─────▼──────┐  │                        │                  │
│  │  Bridge    │  │                        │                  │
│  │  (Python)  │  │                        │                  │
│  └────────────┘  │                        │                  │
└──────────────────┘                        └──────────────────┘
```

### Transport Options

| Transport       | Pros                        | Cons                        |
| --------------- | --------------------------- | --------------------------- |
| **USB Serial**  | Zero pairing, reliable      | Tethered by cable           |
| **BLE (NUS)**   | Wireless, like the original | Requires pairing, more code |
| **Wi-Fi/HTTP**  | Long range                  | Needs network config        |

Implement **USB serial first**, then BLE as an optional upgrade.

---

## Wire Protocol

Identical framing to claude-desktop-buddy: **newline-delimited UTF-8 JSON**.

### Bridge → Device: Heartbeat (every 2s, or on change)

```json
{
  "state": "busy",
  "query": "regex to validate email addresses",
  "mode": "suggest",
  "queries_today": 12,
  "total_queries": 347,
  "ts": 1775731234
}
```

| Field            | Type   | Description                              |
| ---------------- | ------ | ---------------------------------------- |
| `state`          | string | One of: `sleep`, `idle`, `busy`, `done`, `error` |
| `query`          | string | Current or most recent query text        |
| `mode`           | string | `"suggest"` or `"explain"`               |
| `queries_today`  | int    | Reset at local midnight                  |
| `total_queries`  | int    | Cumulative all-time                      |
| `ts`             | int    | Unix epoch seconds                       |

### Bridge → Device: Events (one-shot)

```json
{"evt": "start", "query": "explain this awk command", "mode": "explain"}
{"evt": "end", "preview": "This command extracts the second field..."}
{"evt": "error", "msg": "gh: command not found"}
{"evt": "milestone", "n": 100}
```

### Device → Bridge: Status (on request)

```json
{
  "ack": "status",
  "ok": true,
  "data": {
    "pet": "octocat",
    "uptime": 8412,
    "heap_free": 84200,
    "display": "ST7789"
  }
}
```

---

## Firmware Implementation

Provide **three implementations** in the repo. Users pick one.

### Option A: CircuitPython (recommended for beginners)

**Dependencies:** `adafruit_display_text`, `adafruit_ssd1306` or
`adafruit_st7789`, `adafruit_ble` (for BLE mode), `json`, `os`

### Option B: MicroPython

**Dependencies:** `st7789_mpy` or `ssd1306`, `ujson`, `machine`

### Option C: Arduino (C++)

**Dependencies:** `TFT_eSPI` or `Adafruit_GFX` + display driver,
`ArduinoJson`

> The spec below uses **CircuitPython** syntax for examples. Arduino and
> MicroPython implementations should mirror the same structure.

---

## Firmware Architecture

```
firmware/
├── circuitpython/
│   ├── code.py               # Main loop
│   ├── config.py             # Pins, display type, serial/BLE toggle
│   ├── state_manager.py      # Event → pet state mapping
│   ├── pet_renderer.py       # ASCII/GIF rendering to display
│   ├── serial_bridge.py      # USB serial JSON reader
│   ├── ble_bridge.py         # BLE NUS JSON reader (optional)
│   ├── display_driver.py     # Display abstraction (TFT vs OLED)
│   ├── stats.py              # Persistent stats (NVS / filesystem)
│   └── pets/
│       ├── octocat.py
│       ├── crab.py
│       ├── fox.py
│       ├── owl.py
│       ├── robot.py
│       └── ghost.py
├── micropython/
│   └── ... (same structure)
├── arduino/
│   ├── copilot_buddy/
│   │   ├── copilot_buddy.ino
│   │   ├── config.h
│   │   ├── state.h / state.cpp
│   │   ├── pet.h / pet.cpp
│   │   ├── ble_bridge.h / ble_bridge.cpp
│   │   ├── display.h / display.cpp
│   │   └── buddies/          # One .h per pet species
│   └── platformio.ini
└── README.md
```

---

## Pet System

### Seven States

| State       | Trigger                              | Animation Feel               |
| ----------- | ------------------------------------ | ---------------------------- |
| `sleep`     | No activity for > 5 min             | Eyes closed, slow breathing  |
| `idle`      | Bridge connected, no active query    | Blinking, looking around     |
| `busy`      | Copilot CLI process running          | Sweating, working hard       |
| `attention` | Response ready                       | Alert, bouncing              |
| `celebrate` | Milestone (every 50 queries)         | Confetti, dancing            |
| `dizzy`     | Error detected                       | Spiral eyes, wobbling        |
| `heart`     | Query completed in < 3 seconds       | Floating hearts              |

### ASCII Pet Format

Each pet defines frames for each state as multi-line strings:

```python
# pets/octocat.py

PET = {
    "name": "octocat",
    "frames": {
        "sleep": [
            "  ╱|、\n"
            " (˘ ˘ zzZ\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ"
        ],
        "idle": [
            "  ╱|、\n"
            " (• ω •)\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ",
            # ---
            "  ╱|、\n"
            " (• ω •)?\n"
            "  ꜝ |、\n"
            "  ~じし_)ノ"
        ],
        "busy": [
            "  ╱|、\n"
            " (◎_◎;)\n"
            "  ꜝ |、⌨️\n"
            "  ~じし_)ノ"
        ],
        # ... etc
    }
}
```

### GIF Pet Support (TFT only)

For color TFT displays, optionally support GIF character packs in the
same format as claude-desktop-buddy:

```
pets_gif/
└── octocat/
    ├── manifest.json
    ├── sleep.gif
    ├── idle.gif
    ├── busy.gif
    ├── attention.gif
    ├── celebrate.gif
    ├── dizzy.gif
    └── heart.gif
```

GIFs should be resized to match the display width (e.g., 96px for 135px
displays, 120px for 240px displays).

---

## Host Bridge Script

A Python script that runs on the user's computer and sends events to the
ESP32.

```
bridge/
├── copilot_bridge.py       # Main bridge script
├── watcher.py              # Process table / history monitor
├── transport_serial.py     # USB serial sender
├── transport_ble.py        # BLE NUS sender (optional)
├── requirements.txt        # psutil, pyserial, bleak (optional)
└── README.md
```

### `watcher.py`

```python
"""
Monitor for Copilot CLI activity (both `gh copilot` and standalone `copilot`).

Detection methods (in priority order):
1. Process table scanning via psutil — look for Copilot CLI processes
   (both 'gh copilot' and standalone 'copilot' executables)
2. Shell history tailing — watch ~/.zsh_history, ~/.bash_history,
   or ~/.local/share/fish/fish_history for new Copilot CLI entries
"""

import psutil
import time

def scan_processes():
    """Return list of active Copilot CLI processes with their args."""
    results = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline'] or []
            name = (proc.info.get('name') or '').lower()
            basename = name.removesuffix('.exe')
            joined = ' '.join(cmdline).lower()

            # Traditional: `gh copilot suggest/explain`
            is_gh_copilot = basename == 'gh' and 'copilot' in joined
            # Standalone: `copilot --yolo --experimental`
            is_standalone = basename == 'copilot'

            if not is_gh_copilot and not is_standalone:
                continue

            mode = 'explain' if 'explain' in joined else 'suggest'
            query = extract_query(cmdline)
            results.append({'pid': proc.info['pid'],
                            'mode': mode,
                            'query': query})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return results

class CopilotWatcher:
    def __init__(self, poll_interval=2):
        self.poll_interval = poll_interval
        self.active_pids = set()
        self.state = 'idle'

    def poll(self):
        procs = scan_processes()
        current_pids = {p['pid'] for p in procs}

        new = current_pids - self.active_pids
        ended = self.active_pids - current_pids

        events = []
        for pid in new:
            p = next(x for x in procs if x['pid'] == pid)
            events.append({'evt': 'start',
                           'query': p['query'],
                           'mode': p['mode']})

        for pid in ended:
            events.append({'evt': 'end', 'preview': ''})

        self.active_pids = current_pids
        self.state = 'busy' if current_pids else 'idle'
        return events
```

### `copilot_bridge.py`

```python
"""
Main bridge: polls watcher, sends JSON heartbeats over serial or BLE.

Usage:
  python copilot_bridge.py                    # auto-detect serial port
  python copilot_bridge.py --port /dev/ttyUSB0
  python copilot_bridge.py --ble              # use BLE instead
"""

import argparse, json, time
from watcher import CopilotWatcher

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='auto')
    parser.add_argument('--ble', action='store_true')
    parser.add_argument('--baud', type=int, default=115200)
    args = parser.parse_args()

    transport = init_transport(args)
    watcher = CopilotWatcher()

    while True:
        events = watcher.poll()
        for evt in events:
            transport.send(json.dumps(evt) + '\n')

        heartbeat = {
            'state': watcher.state,
            'queries_today': watcher.queries_today,
            'total_queries': watcher.total_queries,
            'ts': int(time.time())
        }
        transport.send(json.dumps(heartbeat) + '\n')
        time.sleep(2)
```

---

## Full Project Layout

```
copilot-buddy/
├── README.md
├── LICENSE                      # MIT
├── docs/
│   └── wiring.md               # Pin diagrams per board
│
├── bridge/                      # Runs on your computer
│   ├── copilot_bridge.py
│   ├── watcher.py
│   ├── transport_serial.py
│   ├── transport_ble.py
│   ├── requirements.txt
│   └── README.md
│
├── firmware/
│   ├── circuitpython/
│   │   ├── code.py
│   │   ├── config.py
│   │   ├── state_manager.py
│   │   ├── pet_renderer.py
│   │   ├── serial_bridge.py
│   │   ├── ble_bridge.py
│   │   ├── display_driver.py
│   │   ├── stats.py
│   │   └── pets/
│   │       ├── octocat.py
│   │       ├── crab.py
│   │       ├── fox.py
│   │       ├── owl.py
│   │       ├── robot.py
│   │       └── ghost.py
│   │
│   ├── micropython/
│   │   └── ...                  # Same structure as circuitpython
│   │
│   └── arduino/
│       ├── copilot_buddy/
│       │   ├── copilot_buddy.ino
│       │   ├── config.h
│       │   ├── state.h
│       │   ├── state.cpp
│       │   ├── pet.h
│       │   ├── pet.cpp
│       │   ├── display.h
│       │   ├── display.cpp
│       │   ├── ble_bridge.h
│       │   ├── ble_bridge.cpp
│       │   └── buddies/
│       │       ├── octocat.h
│       │       ├── crab.h
│       │       └── ...
│       └── platformio.ini
│
├── pets_gif/                    # Optional GIF character packs
│   └── octocat/
│       ├── manifest.json
│       └── *.gif
│
└── tools/
    ├── prep_character.py        # Resize GIFs for target display
    └── flash_character.py       # Push GIF pack over USB
```

---

## Implementation Order

### Phase 1 — Hello World
1. Wire up ESP32 + display
2. Get a static ASCII art character rendering on screen
3. Confirm USB serial echo (send JSON in, parse it, print to serial)

### Phase 2 — Bridge MVP
4. Implement `watcher.py` with process scanning
5. Implement `transport_serial.py`
6. Implement `copilot_bridge.py` — send heartbeats over serial
7. Test: run `gh copilot suggest` or `copilot` and confirm bridge detects it

### Phase 3 — Firmware State Machine
8. Implement `serial_bridge.py` on device — read JSON from USB
9. Implement `state_manager.py` — map heartbeats to pet states
10. Implement `pet_renderer.py` — swap ASCII frames based on state
11. End-to-end test: run a Copilot query, watch the pet react

### Phase 4 — Pets & Polish
12. Create all 6 pets with all 7 states
13. Add pet selection (button press cycles through pets)
14. Add stats display screen (queries today, total, uptime)
15. Add persistent stats (NVS on Arduino, filesystem on Python)
16. Add screen auto-off after 30s idle, wake on button or state change

### Phase 5 — BLE (Optional)
17. Implement BLE NUS on device (`ble_bridge.py` or `ble_bridge.cpp`)
18. Implement `transport_ble.py` on host using `bleak`
19. Add pairing flow

### Phase 6 — GIF Support (Optional)
20. Implement GIF decoder for TFT displays
21. Port the folder-push protocol from claude-desktop-buddy
22. Add `tools/prep_character.py`

---

## Acceptance Criteria

- [ ] ESP32 displays an animated ASCII pet on attached screen
- [ ] Pet state changes in real time when Copilot CLI runs (`gh copilot suggest/explain` or standalone `copilot`)
- [ ] At least 6 selectable pets with 7 animation states each
- [ ] Host bridge script auto-detects serial port and sends heartbeats
- [ ] Stats (queries today, total) persist across reboots
- [ ] Works with at least 2 display types (one OLED, one TFT)
- [ ] CircuitPython implementation fully functional
- [ ] At least one additional implementation (MicroPython or Arduino)
- [ ] Screen auto-off after 30s idle
- [ ] Button press cycles pets and wakes screen
- [ ] README with wiring diagrams, setup instructions, and photos

---

## Acknowledgements

Inspired by [claude-desktop-buddy](https://github.com/anthropics/claude-desktop-buddy)
by Anthropic, licensed under MIT.