---
name: orchestrated-build
description: Auto-detect project ecosystem and run the full multi-agent implementation workflow — use this instead of picking a specific ecosystem skill
---

# Orchestrated Build — Auto-detect Ecosystem

Detect the project ecosystem by scanning the workspace root for marker files, then delegate to the correct orchestrator.

## Detection table (check in this order — first match wins)

| Marker combination | Ecosystem | Orchestrator |
|---|---|---|
| `Cargo.toml` + `package.json` + `tauri.conf.json` (or `src-tauri/`) | Tauri | `tauri-orchestrator` |
| `Package.swift` or `*.xcodeproj` or `*.xcworkspace` | Swift/iOS | `swift-orchestrator` |
| `build.gradle` or `build.gradle.kts` + `AndroidManifest.xml` (or `app/src/main/`) | Kotlin/Android | `kotlin-orchestrator` |
| `Cargo.toml` (no Tauri markers) | Rust | `rust-orchestrator` |
| `package.json` + `tsconfig.json` | TypeScript | `typescript-orchestrator` |
| `code.py` + `lib/` with `adafruit_*` packages | CircuitPython | `circuitpython-orchestrator` |
| `boot.py` or `main.py` with `machine` module imports | MicroPython | `micropython-orchestrator` |
| `*.ino` files or `sketch.yaml` or Arduino library structure (`library.properties`) | Arduino | `arduino-orchestrator` |
| `pyproject.toml` or `setup.py` or `requirements.txt` | Python | `python-orchestrator` |

## Steps

1. Check for each marker combination above, in order. Use file reads or search to verify.
2. If a clear single ecosystem is detected, delegate immediately to that orchestrator with the user's full task.
3. If multiple ecosystems are detected (e.g., both `pyproject.toml` and `package.json` without Tauri), ask the user which ecosystem this task targets.
4. If no ecosystem is detected, ask the user which orchestrator to use.
5. For ambiguous MicroPython vs CircuitPython, check for `board` module + `adafruit_*` imports (CircuitPython) vs `machine` module imports (MicroPython). If still ambiguous, ask.

## Delegation

Pass the user's original request verbatim to the detected orchestrator.
