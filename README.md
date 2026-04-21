# copilot-buddy

An ESP32-S2/S3 desk pet that reacts to GitHub Copilot CLI activity in real time.

Inspired by [claude-desktop-buddy](https://github.com/anthropics/claude-desktop-buddy) by Anthropic.

![License: MIT](https://img.shields.io/badge/license-MIT-blue)

---

## What Is This?

A small animated character lives on your desk, displayed on a TFT or OLED screen connected to an ESP32-S2 or ESP32-S3. When you use the Copilot CLI — whether `gh copilot suggest`, `gh copilot explain`, or the standalone `copilot` command — the pet reacts, working hard while your query runs, celebrating milestones, and sleeping when idle.

### Pet States

| State       | Trigger                              | Animation             |
|-------------|--------------------------------------|-----------------------|
| 💤 Sleep    | No activity for 5+ minutes          | Eyes closed, breathing |
| 😊 Idle     | Bridge connected, no active query    | Blinking, looking around |
| 💻 Busy     | Copilot CLI query running            | Sweating, typing      |
| ❗ Attention | Response ready                       | Alert, bouncing       |
| 🎉 Celebrate| Milestone (every 50 queries)         | Dancing, confetti     |
| 😵 Dizzy    | Error detected                       | Spiral eyes, wobbling |
| 💕 Heart    | Query completed in < 3 seconds       | Floating hearts       |

### Choose Your Pet

Six ASCII art pets included: **Octocat**, **Crab**, **Fox**, **Owl**, **Robot**, **Ghost**. Cycle through them with a long press.

---

## Supported Hardware

| Board                          | Display        | Notes                           |
|-------------------------------|----------------|--------------------------------|
| **ESP32-S3 DevKit + ST7789**  | 240×240 TFT    | Default — good balance          |
| **ESP32-S3 DevKit + SSD1306** | 128×64 OLED    | Cheapest, ASCII-only            |
| **ESP32-S3 DevKit + ILI9341** | 240×320 TFT    | Largest screen                  |
| **M5StickC Plus2**            | 135×240 TFT    | All-in-one, no wiring needed   |
| **LILYGO T-Display-S3**      | 170×320 TFT    | Built-in display, USB-C        |
| **QT Py ESP32-S2 + SSD1306** | 128×64 OLED    | STEMMA QT plug-and-play, no BLE |
| **QT Py ESP32-S2 + ST7789**  | 240×240 TFT    | Tiny board, SPI wiring, no BLE  |
| **QT Py ESP32-S2 + ILI9341** | 240×320 TFT    | Tiny board, SPI wiring, no BLE  |
| **QT Py ESP32-S2 + EYESPI BFF + ILI9341** | 240×320 TFT | Via EYESPI FPC cable, no loose wires, no BLE |
| **QT Py ESP32-S3 + SSD1306** | 128×64 OLED    | STEMMA QT plug-and-play         |
| **QT Py ESP32-S3 + ST7789**  | 240×240 TFT    | Tiny board, SPI wiring          |
| **QT Py ESP32-S3 + ILI9341** | 240×320 TFT    | Tiny board, SPI wiring          |

See [docs/wiring.md](docs/wiring.md) for pin diagrams.

---

## Quick Start

### 1. Flash firmware to your ESP32

Three firmware options are provided — pick one:

| Option | Directory | Best for |
|--------|-----------|----------|
| **CircuitPython** (recommended) | `firmware/circuitpython/` | Beginners, fast iteration |
| **MicroPython** | `firmware/micropython/` | MicroPython users |
| **Arduino (C++)** | `firmware/arduino/` | Performance, C++ developers |

**CircuitPython setup:**
1. Install [CircuitPython 10.x](https://circuitpython.org/downloads) on your ESP32-S2 or ESP32-S3
2. Install libraries: `adafruit_st7789` (or your display driver), `adafruit_display_text` — plus `adafruit_focaltouch` and `adafruit_bus_device` if your display has capacitive touch
3. Edit `config.py` — uncomment your board
4. Copy all files from `firmware/circuitpython/` to the `CIRCUITPY` drive
5. **Hard reset** the board — `boot.py` takes effect on hard reset and disables the USB drive on ESP32-S2 (use safe mode to copy files afterward; see `firmware/circuitpython/README.md`)

### 2. Connect to Copilot CLI

Two options — pick one:

#### Option A: Hook mode (recommended — no daemon needed)

Uses the standalone Copilot CLI's native hook system. Use daemon mode instead
if you want support for `gh copilot suggest` / `gh copilot explain`.

From the repository root:

```bash
python -m venv .venv            # one-time setup
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

python -m pip install -r bridge/requirements.txt
```

Configure the serial port (pick one method):
- **Windows PowerShell:** `$env:COPILOT_BUDDY_PORT = "COM7"`
- **Linux/macOS shell:** `export COPILOT_BUDDY_PORT=/dev/ttyACM0`
- **Config file:** Create `.copilot-buddy.local.json` in the repo root: `{"serial_port": "COM7"}`
- **Auto-detect:** Leave unconfigured — the bridge tries USB VID matching first, then a handshake probe, then USB description matching

Then just use Copilot CLI from within this repo (or a subdirectory) — hooks fire automatically.

> **Note:** The hook scripts resolve Python at runtime via `py -3` / `python3` / `python` from `PATH`, which may not be your virtual environment's Python. If hooks cannot find `pyserial`, either install it in the Python that hooks resolve, or update the hook script to use your venv interpreter.

#### Option B: Daemon mode

Run a long-lived bridge process that polls for Copilot CLI activity.
All commands are run from the **repository root** with the virtual environment activated:

```bash
python -m venv .venv            # one-time setup (skip if already created)
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

python -m pip install -r bridge/requirements.txt
python -m bridge.copilot_bridge
```

The bridge auto-detects the ESP32 serial port. Use `--port COM3` (Windows) or `--port /dev/ttyACM0` (Linux) to specify manually.

### 3. Use Copilot and watch your pet react!

```bash
# Hook mode
copilot --yolo --experimental

# Daemon mode
gh copilot suggest "how to reverse a linked list"
```

Your desk pet will transition: idle → busy → attention → idle.

---

## Architecture

```
┌──────────────────┐        USB Serial       ┌──────────────────┐
│   Your Computer  │  ──────────────────▶   │  ESP32-S2/S3     │
│                  │    JSON messages        │                  │
│  ┌────────────┐  │    (newline-delim)      │  ┌────────────┐  │
│  │Copilot CLI │  │                        │  │  Display    │  │
│  └─────┬──────┘  │                        │  │  + Pet      │  │
│  ┌─────▼──────┐  │                        │  └────────────┘  │
│  │  Bridge    │  │                        │                  │
│  │  (Python)  │  │                        │                  │
│  └────────────┘  │                        │                  │
└──────────────────┘                        └──────────────────┘
```

The bridge connects to the ESP32 using two modes: **hook mode** uses Copilot CLI's native `.github/hooks/` system for zero-daemon operation (each CLI event fires a short-lived Python process), while **daemon mode** polls for processes using `psutil` and file watching. Both send JSON heartbeats/events over USB serial. See [protocol/schema.md](protocol/schema.md) for the wire protocol.

---

## Project Structure

```
copilot-buddy/
├── .github/hooks/               # Copilot CLI hook integration
│   ├── copilot-buddy.json       # Hook event registration
│   ├── run-hook.ps1             # PowerShell wrapper
│   └── run-hook.sh              # Bash wrapper
├── bridge/                      # Host-side bridge (CPython)
│   ├── constants.py             # Shared protocol constants
│   ├── copilot_bridge.py        # Daemon mode bridge script
│   ├── hook_bridge/             # Hook mode bridge (no daemon)
│   ├── watcher.py               # Process scanner (gh copilot)
│   ├── cli_watcher.py           # File watcher (standalone copilot)
│   ├── transport_serial.py      # USB serial transport
│   └── tests/                   # pytest test suite
├── firmware/
│   ├── circuitpython/           # CircuitPython firmware
│   ├── micropython/             # MicroPython firmware
│   └── arduino/                 # Arduino/PlatformIO firmware
├── protocol/                    # Wire protocol spec + test fixtures
│   ├── schema.md
│   ├── fixtures/                # JSON test data
│   └── replay.py               # Fixture replay tool
├── docs/
│   └── wiring.md               # Pin diagrams per board
└── tools/                       # Utilities
```

---

## Features

- ✅ 6 animated ASCII pets with 7 states each
- ✅ Real-time Copilot CLI activity detection
- ✅ Persistent query stats across reboots
- ✅ Screen auto-off after 30s idle, wake on activity
- ✅ HUD transcript: 5-line activity log at the bottom of the display (repo + HH:MM + query)
- ✅ Button: short press scrolls transcript, long press cycles pets
- ✅ Capacitive touch: tap scrolls HUD, horizontal swipe cycles pets (FT6206, optional)
- ✅ Works with many board/display combinations (see table above)
- ✅ Three firmware options (CircuitPython, MicroPython, Arduino)
- ✅ Protocol test fixtures for development without hardware

---

## Development

All commands below assume you are in the **repository root** with the virtual environment activated.

### Bridge tests
```bash
python -m pip install -r bridge/requirements.txt
python -m pip install pytest
python -m pytest bridge/tests/ -v
```

### Protocol replay (test firmware without the bridge)

Requires `pyserial` (already in `bridge/requirements.txt`):

```bash
python protocol/replay.py protocol/fixtures/full_session.jsonl --port COM3
```

### Linting

Requires `ruff` (`python -m pip install ruff`):

```bash
python -m ruff check bridge/ protocol/ firmware/circuitpython/ firmware/micropython/
```

---

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

Inspired by [claude-desktop-buddy](https://github.com/anthropics/claude-desktop-buddy) by Anthropic.
