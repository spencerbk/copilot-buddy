# copilot-buddy Bridge

The bridge monitors your computer for GitHub Copilot CLI activity (`gh copilot suggest` / `gh copilot explain` or the standalone `copilot` CLI) and streams real-time events to the ESP32 desk-pet over USB serial. It scans the process table with psutil, detects when Copilot queries start and end, tracks daily usage stats, and sends heartbeats so the pet always knows you're there.

## Requirements

- **Python** 3.10 or later
- **OS:** Windows (primary target), macOS and Linux also supported
- **Hardware:** ESP32 desk-pet connected via USB (not needed for testing)

## Installation

```bash
cd bridge
pip install -r requirements.txt
```

## Usage

Run from the **repository root**:

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

## How it works

1. **Process scanning** — Every `--poll-interval` seconds the bridge calls `psutil.process_iter()` and looks for Copilot CLI processes by executable name (`gh` with `copilot` in the arguments, or the standalone `copilot` executable).
2. **CLI file watcher** — Watches `~/.copilot/` for file changes to detect per-turn activity in the standalone `copilot` CLI. Provides query text from `command-history-state.json` and turn-end detection via `events.jsonl` quiescence.
3. **Event detection** — When a new Copilot process appears a `start` event is emitted; when it disappears an `end` event is emitted and the daily query counter increments. Both watchers feed a shared activity log.
4. **Heartbeat** — Every 2 seconds the bridge sends a heartbeat message containing the current state (`idle` / `busy`), `queries_today`, `total_queries`, a one-line `msg` summary, and a recent `entries` activity log for the device's HUD transcript.
5. **Serial transport** — Messages are newline-delimited JSON sent over USB serial at 115200 baud. The bridge can auto-detect the correct COM port by sending a `{"cmd":"status"}` handshake and waiting for an `{"ack":"status"}` reply.

## Running tests

```bash
pip install pytest
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
