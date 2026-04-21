# copilot-buddy Bridge

The bridge connects your computer to the ESP32 desk-pet, streaming real-time Copilot CLI events over USB serial. It works across **all your repos and terminal sessions** — you install it once in this repo and leave it running.

| Mode | How it works | Scope |
|------|-------------|-------|
| **Daemon mode** (recommended) | Long-running process watches all Copilot CLI activity | All repos, all terminals |
| **Hook mode** | Copilot CLI's native hooks push events directly | Only inside repos with `.github/hooks/` |

## Requirements

- **Python** 3.10 or later
- **OS:** Windows (primary target), macOS and Linux also supported
- **Hardware:** ESP32 desk-pet connected via USB (not needed for testing)

> **Convention:** All commands below assume you are in the **repository root** (`copilot-buddy/`) with the virtual environment activated.

## Installation

Create a virtual environment at the repository root and install dependencies:

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r bridge\requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r bridge/requirements.txt
```

Activate the virtual environment (`Activate.ps1` or `source .venv/bin/activate`) each time you open a new terminal before running bridge, daemon, or test commands.

## Daemon Mode (recommended)

The daemon monitors Copilot CLI activity across **all repos and terminal sessions** by polling the process table and watching `~/.copilot/` for file changes. This is the primary way to use copilot-buddy — install once, leave it running, and use Copilot CLI anywhere.

```bash
# Auto-detect the ESP32 serial port
python -m bridge.copilot_bridge

# Explicit serial port
python -m bridge.copilot_bridge --port COM3

# Verbose / debug logging
python -m bridge.copilot_bridge -v

# Testing mode (no hardware needed)
python -m bridge.copilot_bridge --transport loopback
```

### Command-line options

| Flag | Default | Description |
|---|---|---|
| `--port PORT` | `auto` | Serial port (`COM3`, `/dev/ttyUSB0`, etc.) |
| `--baud RATE` | `115200` | Serial baud rate |
| `--transport {serial,loopback}` | `serial` | Transport backend |
| `--poll-interval SECS` | `1.0` | Process scan interval |
| `--copilot-dir DIR` | auto | Path to `~/.copilot` directory |
| `-v, --verbose` | off | Enable debug logging |

## Hook Mode (advanced — per-repo only)

Uses the standalone Copilot CLI's `.github/hooks/` system — no background script needed. Copilot CLI invokes a short-lived Python process on each lifecycle event (session start, tool use, agent stop, etc.).

Hooks provide **richer event detail** than daemon mode (tool names, error types, query text) but only work when Copilot CLI is invoked inside a repo that contains the hook scripts. This is primarily useful for developing copilot-buddy itself, or if you copy the `.github/hooks/` directory into your other projects.

### Setup

1. Flash the firmware to your ESP32 (see the main README).
2. Configure the serial port (pick one):
   - **Windows PowerShell:** `$env:COPILOT_BUDDY_PORT = "COM7"`
   - **Linux/macOS shell:** `export COPILOT_BUDDY_PORT=/dev/ttyACM0`
   - **Config file:** Create `.copilot-buddy.local.json` in the repo root:
     ```json
     {
       "serial_port": "COM7"
     }
     ```
   - **Auto-detect:** If neither is set, the bridge tries USB VID matching (Adafruit / Espressif), then falls back to a status-handshake probe, then USB description matching.
3. Run Copilot CLI from within this repository (or a subdirectory) — hooks load automatically from `.github/hooks/`.

That's it. The pet reacts to Copilot CLI activity with no daemon running.

> **Note on hooks and Python:** The hook scripts (`.github/hooks/run-hook.ps1` / `run-hook.sh`) resolve Python at runtime using `py -3`, `python3`, or `python` from your `PATH`. This may not be the same Python as your repo virtual environment. If hooks fail to send serial data, ensure `pyserial` is installed in whichever Python the hook script finds, or update the hook script to point to your venv's Python.

### Hook events

| Copilot CLI Event | Pet Reaction |
|---|---|
| `sessionStart` | Wake up (idle) |
| `userPromptSubmitted` | Start working (busy) |
| `preToolUse` / `postToolUse` | Stay busy, show tool name |
| `postToolUseFailure` | Dizzy (error) |
| `agentStop` | Done — heart (fast) or attention (normal) |
| `errorOccurred` | Dizzy |
| `sessionEnd` | Sleep |

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `COPILOT_BUDDY_PORT` | *(auto-detect)* | Serial port (e.g., `COM7`, `/dev/ttyACM0`) |
| `COPILOT_BUDDY_BAUD` | `115200` | Baud rate |
| `COPILOT_BUDDY_DRY_RUN` | `false` | If `true`, log messages to stderr instead of sending |
| `COPILOT_BUDDY_LOG_LEVEL` | `WARNING` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### Debugging hooks

Set `COPILOT_BUDDY_LOG_LEVEL=DEBUG` to see all hook events and serial traffic on stderr. Use `COPILOT_BUDDY_DRY_RUN=true` to test without hardware.

## How it works

1. **Process scanning** — Every `--poll-interval` seconds the bridge calls `psutil.process_iter()` and looks for Copilot CLI processes by executable name (`gh` with `copilot` in the arguments, or the standalone `copilot` executable).
2. **CLI file watcher** — Watches `~/.copilot/` for file changes to detect per-turn activity in the standalone `copilot` CLI. Provides query text from `command-history-state.json` and turn-end detection via `events.jsonl` quiescence.
3. **Event detection** — When a new Copilot process appears a `start` event is emitted; when it disappears an `end` event is emitted and the daily query counter increments. Both watchers feed a shared activity log.
4. **Heartbeat** — Every 2 seconds the bridge sends a heartbeat message containing the current state (`idle` / `busy`), `queries_today`, `total_queries`, a one-line `msg` summary, and a recent `entries` activity log for the device's HUD transcript.
5. **Serial transport** — Messages are newline-delimited JSON sent over USB serial at 115200 baud. The bridge can auto-detect the correct COM port by matching known USB vendor IDs (Adafruit, Espressif), sending a `{"cmd":"status"}` handshake, or falling back to USB description matching.

## Running tests

From the repository root with the virtual environment activated:

```bash
python -m pip install pytest
python -m pytest bridge/tests/ -v
```

## Troubleshooting

### "No ESP32 device found"

- Check the USB cable is plugged in and the device is powered on.
- Make sure `boot.py` on the ESP32 is configured to enable USB serial.
- Try specifying the port explicitly: `--port COM3` (Windows) or `--port /dev/ttyUSB0` (Linux).

### "Serial write failed"

The device may have disconnected. The bridge will automatically attempt to reconnect every 5 seconds. Ensure the cable is seated firmly.

### Process detection misses short-lived queries

This is expected. The bridge polls at a configurable interval (default 1 s), so Copilot invocations that start and finish within a single polling window may not be detected. Lowering `--poll-interval` can help but increases CPU usage.

## Known limitations

- **Poll-based detection** — very fast Copilot invocations (< 1 s) can be missed entirely.
- **Windows focus** — tested primarily on Windows; macOS/Linux support is best-effort.
- **Single device** — the bridge connects to one ESP32 at a time.
- **No query content from the Copilot response** — only the user's input query is captured, not the AI-generated answer.
