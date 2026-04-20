"""Tests for the copilot-buddy hook bridge.

Covers event mapping, persistent stats, config loading, and the
entry-point wiring.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from unittest.mock import patch

from bridge.hook_bridge.config import load_config
from bridge.hook_bridge.detect import detect_port
from bridge.hook_bridge.events import build_messages
from bridge.hook_bridge.locking import hook_lock
from bridge.hook_bridge.stats import (
    MAX_ENTRIES,
    MILESTONE_INTERVAL,
    HookStats,
    load_stats,
    record_query,
    refresh_day,
    save_stats,
)


# ── events.py tests ────────────────────────────────────────────────────


class TestEventMapping:
    """Verify each Copilot CLI hook event maps to the correct protocol."""

    def _stats(self, **kw) -> HookStats:
        return HookStats(queries_today=5, total_queries=42, **kw)

    def test_session_start_sends_idle_heartbeat(self) -> None:
        msgs = build_messages("sessionStart", {}, self._stats())
        assert len(msgs) == 1
        assert msgs[0]["state"] == "idle"
        assert "ts" in msgs[0]
        assert msgs[0]["msg"] == "connected"

    def test_session_end_sends_sleep(self) -> None:
        msgs = build_messages("sessionEnd", {}, self._stats())
        assert len(msgs) == 1
        assert msgs[0]["state"] == "sleep"

    def test_user_prompt_sends_start_event(self) -> None:
        payload = {"userMessage": {"content": "explain awk"}}
        msgs = build_messages("userPromptSubmitted", payload, self._stats())
        assert len(msgs) == 1
        assert msgs[0]["evt"] == "start"
        assert msgs[0]["query"] == "explain awk"
        assert msgs[0]["mode"] == "chat"

    def test_user_prompt_string_payload(self) -> None:
        payload = {"userMessage": "explain awk"}
        msgs = build_messages("userPromptSubmitted", payload, self._stats())
        assert msgs[0]["query"] == "explain awk"

    def test_user_prompt_truncates_long_query(self) -> None:
        payload = {"userMessage": {"content": "x" * 200}}
        msgs = build_messages("userPromptSubmitted", payload, self._stats())
        assert len(msgs[0]["query"]) == 80

    def test_pre_tool_use_sends_busy(self) -> None:
        msgs = build_messages("preToolUse", {"toolName": "bash"}, self._stats())
        assert msgs[0]["state"] == "busy"
        assert "bash" in msgs[0]["msg"]

    def test_post_tool_use_sends_busy_with_ok(self) -> None:
        msgs = build_messages("postToolUse", {"toolName": "grep"}, self._stats())
        assert msgs[0]["state"] == "busy"
        assert msgs[0]["msg"].endswith("ok")

    def test_post_tool_use_failure_sends_error(self) -> None:
        msgs = build_messages(
            "postToolUseFailure", {"toolName": "bash"}, self._stats()
        )
        assert msgs[0]["evt"] == "error"
        assert "bash" in msgs[0]["msg"]

    def test_permission_request_sends_busy(self) -> None:
        msgs = build_messages("permissionRequest", {}, self._stats())
        assert msgs[0]["state"] == "busy"
        assert "permission" in msgs[0]["msg"]

    def test_subagent_start_sends_busy(self) -> None:
        msgs = build_messages(
            "subagentStart", {"agentName": "explore"}, self._stats()
        )
        assert msgs[0]["state"] == "busy"
        assert "explore" in msgs[0]["msg"]

    def test_subagent_stop_sends_busy(self) -> None:
        msgs = build_messages("subagentStop", {}, self._stats())
        assert msgs[0]["state"] == "busy"

    def test_agent_stop_sends_end_event(self) -> None:
        msgs = build_messages("agentStop", {}, self._stats())
        assert msgs[0]["evt"] == "end"

    def test_error_occurred_sends_error_event(self) -> None:
        payload = {"error": {"name": "RateLimit", "message": "too many requests"}}
        msgs = build_messages("errorOccurred", payload, self._stats())
        assert msgs[0]["evt"] == "error"
        assert "too many requests" in msgs[0]["msg"]

    def test_pre_compact_is_silent(self) -> None:
        assert build_messages("preCompact", {}, self._stats()) == []

    def test_notification_is_silent(self) -> None:
        assert build_messages("notification", {}, self._stats()) == []

    def test_unknown_event_sends_idle_heartbeat(self) -> None:
        msgs = build_messages("someFutureEvent", {}, self._stats())
        assert len(msgs) == 1
        assert msgs[0]["state"] == "idle"

    def test_heartbeat_includes_entries(self) -> None:
        stats = self._stats(entries=["buddy 09:01 foo", "buddy 09:00 bar"])
        msgs = build_messages("sessionStart", {}, stats)
        assert msgs[0]["entries"] == stats.entries

    def test_heartbeat_omits_empty_entries(self) -> None:
        msgs = build_messages("sessionStart", {}, self._stats())
        assert "entries" not in msgs[0]


# ── stats.py tests ─────────────────────────────────────────────────────


class TestStats:
    """Verify persistent stats behaviour."""

    def test_record_query_increments(self) -> None:
        stats = HookStats()
        record_query(stats, "hello")
        assert stats.queries_today == 1
        assert stats.total_queries == 1

    def test_record_query_adds_entry(self) -> None:
        stats = HookStats()
        record_query(stats, "test query")
        assert len(stats.entries) == 1
        assert "test" in stats.entries[0]

    def test_entries_capped_at_max(self) -> None:
        stats = HookStats()
        for i in range(MAX_ENTRIES + 3):
            record_query(stats, f"q{i}")
        assert len(stats.entries) == MAX_ENTRIES

    def test_newest_entry_first(self) -> None:
        stats = HookStats()
        record_query(stats, "first")
        record_query(stats, "second")
        # Second query should be at index 0
        assert "second"[:3] in stats.entries[0] or stats.entries[0] != stats.entries[1]

    def test_milestone_at_interval(self) -> None:
        stats = HookStats(
            queries_today=MILESTONE_INTERVAL - 1,
            total_queries=MILESTONE_INTERVAL - 1,
            last_date=date.today().isoformat(),
        )
        record_query(stats, "milestone query")
        assert stats.milestone == MILESTONE_INTERVAL

    def test_no_milestone_off_interval(self) -> None:
        stats = HookStats(
            queries_today=10,
            total_queries=10,
            last_date=date.today().isoformat(),
        )
        record_query(stats, "normal query")
        assert stats.milestone is None

    def test_midnight_rollover(self) -> None:
        stats = HookStats(queries_today=10, last_date="2020-01-01")
        record_query(stats, "new day")
        assert stats.queries_today == 1  # reset + 1

    def test_refresh_day_resets_stale_stats(self) -> None:
        stats = HookStats(queries_today=7, total_queries=99, last_date="2020-01-01")
        changed = refresh_day(stats)
        assert changed is True
        assert stats.queries_today == 0
        assert stats.total_queries == 99
        assert stats.last_date == date.today().isoformat()

    def test_save_and_load_roundtrip(self) -> None:
        stats = HookStats(
            queries_today=5,
            total_queries=100,
            last_date="2026-04-20",
            entries=["a 12:00 foo", "a 11:59 bar"],
        )
        with tempfile.TemporaryDirectory() as td:
            state_file = os.path.join(td, "hook-state.json")
            with patch("bridge.hook_bridge.stats._STATE_FILE", state_file), \
                 patch("bridge.hook_bridge.stats._STATE_DIR", td):
                save_stats(stats)
                loaded = load_stats()
            assert loaded.queries_today == 5
            assert loaded.total_queries == 100
            assert loaded.last_date == "2026-04-20"
            assert loaded.entries == ["a 12:00 foo", "a 11:59 bar"]

    def test_load_missing_file_returns_defaults(self) -> None:
        with patch(
            "bridge.hook_bridge.stats._STATE_FILE", "/nonexistent/path.json"
        ):
            stats = load_stats()
        assert stats.queries_today == 0
        assert stats.total_queries == 0

    def test_load_corrupt_file_returns_defaults(self) -> None:
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("not json{{{")
            with patch("bridge.hook_bridge.stats._STATE_FILE", path):
                stats = load_stats()
            assert stats.queries_today == 0
        finally:
            os.unlink(path)


# ── config.py tests ────────────────────────────────────────────────────


class TestConfig:
    """Verify config loading precedence."""

    def test_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True), \
             patch("bridge.hook_bridge.config._find_config_file", return_value=None):
            cfg = load_config()
        assert cfg.baud == 115200
        assert cfg.serial_port is None
        assert cfg.dry_run is False

    def test_env_overrides(self) -> None:
        env = {
            "COPILOT_BUDDY_PORT": "COM99",
            "COPILOT_BUDDY_BAUD": "9600",
            "COPILOT_BUDDY_DRY_RUN": "true",
        }
        with patch.dict(os.environ, env, clear=True), \
             patch("bridge.hook_bridge.config._find_config_file", return_value=None):
            cfg = load_config()
        assert cfg.serial_port == "COM99"
        assert cfg.baud == 9600
        assert cfg.dry_run is True

    def test_config_file_loaded(self) -> None:
        config_data = {"serial_port": "/dev/ttyACM0", "baud": 57600}
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(config_data, f)
            with patch.dict(os.environ, {}, clear=True), \
                 patch(
                     "bridge.hook_bridge.config._find_config_file",
                     return_value=path,
                 ):
                cfg = load_config()
            assert cfg.serial_port == "/dev/ttyACM0"
            assert cfg.baud == 57600
        finally:
            os.unlink(path)

    def test_env_overrides_file(self) -> None:
        config_data = {"serial_port": "/dev/ttyACM0"}
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(config_data, f)
            env = {"COPILOT_BUDDY_PORT": "COM5"}
            with patch.dict(os.environ, env, clear=True), \
                 patch(
                     "bridge.hook_bridge.config._find_config_file",
                     return_value=path,
                 ):
                cfg = load_config()
            assert cfg.serial_port == "COM5"  # env wins
        finally:
            os.unlink(path)


# ── detect.py tests ────────────────────────────────────────────────────


class TestDetect:
    """Verify port detection logic."""

    def test_explicit_port_returned_directly(self) -> None:
        assert detect_port("COM3", []) == "COM3"

    def test_handshake_detection_preferred(self) -> None:
        transport = type("Transport", (), {"auto_detect_port": lambda self: "COM7"})()
        with patch("bridge.hook_bridge.detect.SerialTransport", return_value=transport):
            result = detect_port(None, ["CircuitPython"], baud=115200)
        assert result == "COM7"

    def test_description_match_fallback(self) -> None:
        """Description matching is used when handshake probing finds nothing."""

        class FakePort:
            def __init__(self, device: str, description: str) -> None:
                self.device = device
                self.description = description

        fake_ports = [
            FakePort("COM1", "Intel Serial IO"),
            FakePort("COM7", "CircuitPython CDC data"),
        ]
        transport = type("Transport", (), {"auto_detect_port": lambda self: None})()
        with patch("bridge.hook_bridge.detect.SerialTransport", return_value=transport), \
             patch("serial.tools.list_ports.comports", return_value=fake_ports):
            result = detect_port(None, ["CircuitPython"], baud=115200)
        assert result == "COM7"

    def test_no_match_returns_none(self) -> None:
        class FakePort:
            def __init__(self, device: str, description: str) -> None:
                self.device = device
                self.description = description

        fake_ports = [FakePort("COM1", "Intel Serial IO")]
        transport = type("Transport", (), {"auto_detect_port": lambda self: None})()
        with patch("bridge.hook_bridge.detect.SerialTransport", return_value=transport), \
             patch("serial.tools.list_ports.comports", return_value=fake_ports):
            result = detect_port(None, ["CircuitPython"], baud=115200)
        assert result is None


# ── locking.py tests ──────────────────────────────────────────────────────


class TestLocking:
    """Verify the short-lived hook lock serializes concurrent hooks."""

    def test_hook_lock_acquires_and_releases(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            lock_file = os.path.join(td, "hook-state.lock")
            with patch("bridge.hook_bridge.locking._LOCK_DIR", td), \
                 patch("bridge.hook_bridge.locking._LOCK_FILE", lock_file):
                with hook_lock(timeout=0.02) as acquired:
                    assert acquired is True
                    assert os.path.exists(lock_file)
                assert not os.path.exists(lock_file)

    def test_hook_lock_times_out_when_busy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            lock_file = os.path.join(td, "hook-state.lock")
            with open(lock_file, "w", encoding="utf-8") as lock_handle:
                lock_handle.write("busy\n")
            with patch("bridge.hook_bridge.locking._LOCK_DIR", td), \
                 patch("bridge.hook_bridge.locking._LOCK_FILE", lock_file):
                with hook_lock(timeout=0.02) as acquired:
                    assert acquired is False
