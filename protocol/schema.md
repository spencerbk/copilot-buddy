# Copilot Buddy — Wire Protocol

Wire protocol between the host bridge (CPython) and the ESP32 desk pet.

## Transport

- **Physical:** USB CDC serial (ESP32-S2/S3 native USB)
- **Baud rate:** 115 200
- **Framing:** Newline-delimited UTF-8 JSON (`\n` terminator)
- **Max line length:** 512 bytes (messages exceeding this are silently dropped)
- **Encoding:** All strings are UTF-8; no binary payloads

Each message is a single JSON object on one line. The device reads until
`\n`, parses the JSON, and acts on it. Messages that fail to parse are
ignored (the device may increment an error counter).

---

## Bridge → Device

### Heartbeat

Sent every **2 seconds** by the bridge so the device knows the host is
alive and can update its display without polling.

```json
{"state":"busy","mode":"suggest","queries_today":12,"total_queries":347,"ts":1775731234,"msg":"working...","entries":["c-b 10:42 regex for email","c-b 10:39 awk column sum"]}
```

| Field           | Type     | Required | Description                                           |
|-----------------|----------|----------|-------------------------------------------------------|
| `state`         | string   | yes      | One of `sleep`, `idle`, `busy`, `done`, `error`       |
| `mode`          | string   | yes      | `"suggest"`, `"explain"`, or `"chat"`                 |
| `queries_today` | int      | yes      | Queries since local midnight (reset by bridge)        |
| `total_queries` | int      | yes      | Cumulative all-time query count                       |
| `ts`            | int      | yes      | Unix epoch seconds — authoritative clock for device   |
| `msg`           | string   | yes      | One-line HUD summary (e.g. `"working..."`, `"idle"`)  |
| `entries`       | string[] | no       | Recent activity log, newest first (max 5). Omitted when empty. |
| `query`         | string   | no       | Current query text. Omitted when `entries` is present.|

**Entry format:** Each entry is `"<repo> HH:MM <query>"`, truncated to
26 characters (matching the 320 px ILI9341 display at 2× font scale).
The repo prefix is an abbreviation of the current git repository name:
hyphenated names become initials (e.g. `copilot-buddy` → `c-b`),
single-word names are truncated to 6 characters.
The bridge builds entries from both the process watcher
(`gh copilot suggest/explain`) and the CLI file watcher (standalone
`copilot` CLI). The total serialized heartbeat line must stay under
**480 bytes** (the device drops lines exceeding 512 bytes); the bridge
trims entries from oldest if the limit is exceeded.

**State machine (bridge-side):**

```
           start evt
  sleep ──► idle ──► busy ──► done ──► idle
              │                 │
              │    error evt    │
              └────► error ────┘
```

- `sleep` — host machine is idle / screensaver active
- `idle` — Copilot CLI is running but no query in progress
- `busy` — a query is in flight
- `done` — the last query completed successfully
- `error` — the last query failed

The device uses `state` to choose animations. If no heartbeat arrives
within **10 seconds** the device enters a "disconnected" animation.

### Events (one-shot)

Emitted once when something happens. The device may trigger a sound or
animation and then return to the heartbeat-driven state.

#### `start` — query started

```json
{"evt":"start","query":"explain this awk command","mode":"explain"}
```

| Field   | Type   | Required | Description            |
|---------|--------|----------|------------------------|
| `evt`   | string | yes      | Always `"start"`       |
| `query` | string | yes      | The query text         |
| `mode`  | string | yes      | `"suggest"`, `"explain"`, or `"chat"` |

#### `end` — query completed

```json
{"evt":"end","preview":"This command extracts the second field..."}
```

| Field     | Type   | Required | Description                              |
|-----------|--------|----------|------------------------------------------|
| `evt`     | string | yes      | Always `"end"`                           |
| `preview` | string | yes      | First ~80 chars of the Copilot response  |

#### `error` — query failed

```json
{"evt":"error","msg":"gh: command not found"}
```

| Field | Type   | Required | Description       |
|-------|--------|----------|-------------------|
| `evt` | string | yes      | Always `"error"`  |
| `msg` | string | yes      | Error description |

#### `milestone` — query count milestone

```json
{"evt":"milestone","n":50}
```

| Field | Type   | Required | Description                            |
|-------|--------|----------|----------------------------------------|
| `evt` | string | yes      | Always `"milestone"`                   |
| `n`   | int    | yes      | The milestone number (every 50: 50, 100, 150…) |

### Commands

Request information or trigger an action on the device.

#### `status` — request device status

```json
{"cmd":"status"}
```

| Field | Type   | Required | Description        |
|-------|--------|----------|--------------------|
| `cmd` | string | yes      | Always `"status"`  |

---

## Device → Bridge

### Status response

Sent in reply to `{"cmd":"status"}`.

```json
{"ack":"status","ok":true,"data":{"pet":"octocat","uptime":8412,"heap_free":84200,"display":"ST7789"}}
```

| Field  | Type   | Required | Description                              |
|--------|--------|----------|------------------------------------------|
| `ack`  | string | yes      | Echoes the command name (`"status"`)     |
| `ok`   | bool   | yes      | `true` if the device is healthy          |
| `data` | object | yes      | Device-specific telemetry (see below)    |

**`data` fields:**

| Field       | Type   | Description                          |
|-------------|--------|--------------------------------------|
| `pet`       | string | Active pet sprite name               |
| `uptime`    | int    | Seconds since last boot              |
| `heap_free` | int    | Free heap bytes                      |
| `display`   | string | Display controller (e.g. `"ST7789"`) |

---

## Design Notes

1. **Clock sync:** The device has no RTC. It derives wall-clock time from
   the `ts` field in heartbeats.

2. **Idempotency:** Heartbeats are idempotent — re-sending the same state
   is harmless. Events are fire-and-forget; the bridge does not retry.

3. **Future extensibility:** Unknown top-level keys are ignored by both
   sides. New event types can be added by introducing a new `evt` value.

4. **Error budget:** The device silently drops unparseable lines and
   increments `stats.parse_errors`. The bridge can read this via the
   `status` command.

5. **Standalone CLI detection:** The bridge watches files under
   `~/.copilot/` to detect per-turn activity in the standalone
   `copilot` CLI. `command-history-state.json` modifications signal
   turn starts (with query text); `session-state/*/events.jsonl`
   quiescence signals turn ends. These turns use `mode: "chat"`.
   This supplements the process-lifecycle detection used for
   `gh copilot suggest/explain`.
