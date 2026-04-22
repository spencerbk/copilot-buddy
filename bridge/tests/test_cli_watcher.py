"""Tests for bridge.cli_watcher — file-based standalone CLI detection."""

from __future__ import annotations

import json
import os
import time
from datetime import date
from pathlib import Path

from bridge.cli_watcher import CLIWatcher, MAX_QUERY_LEN


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _write_history(path: Path, queries: list[str]) -> None:
    """Write a command-history-state.json file."""
    path.write_text(json.dumps({"commandHistory": queries}), encoding="utf-8")


def _touch_events(session_dir: Path, session_id: str = "abc-123") -> Path:
    """Create a session dir with an events.jsonl file and return its path."""
    sess = session_dir / session_id
    sess.mkdir(parents=True, exist_ok=True)
    events = sess / "events.jsonl"
    events.write_text('{"type":"session.start"}\n', encoding="utf-8")
    return events


def _bump_mtime(path: Path) -> None:
    """Advance a file's mtime so the watcher sees a change."""
    stat = path.stat()
    os.utime(path, (stat.st_atime, stat.st_mtime + 1))


# ------------------------------------------------------------------
# Initialisation
# ------------------------------------------------------------------


class TestInitialisation:
    def test_no_copilot_dir(self, tmp_path: Path) -> None:
        """Non-existent copilot dir → poll returns empty, no crash."""
        w = CLIWatcher(copilot_dir=tmp_path / "does-not-exist")
        assert w.poll() == []

    def test_first_poll_snapshots_without_events(self, tmp_path: Path) -> None:
        """First poll records file state but emits no events."""
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        _write_history(copilot / "command-history-state.json", ["hello"])
        sess_dir = copilot / "session-state"
        _touch_events(sess_dir, "s1")

        w = CLIWatcher(copilot_dir=copilot)
        events = w.poll()  # initialisation poll
        assert events == []
        assert w._initialized is True

    def test_second_poll_no_change_no_events(self, tmp_path: Path) -> None:
        """When nothing changes between polls, no events are emitted."""
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        _write_history(copilot / "command-history-state.json", ["hello"])

        w = CLIWatcher(copilot_dir=copilot)
        w.poll()  # init
        events = w.poll()  # second poll
        assert events == []


# ------------------------------------------------------------------
# Turn start detection (command-history)
# ------------------------------------------------------------------


class TestTurnStart:
    def test_history_change_emits_start(self, tmp_path: Path) -> None:
        """Mtime bump on command-history → start event with query text."""
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["old query"])

        w = CLIWatcher(copilot_dir=copilot)
        w.poll()  # init

        _write_history(hist, ["new query", "old query"])
        _bump_mtime(hist)

        events = w.poll()
        starts = [e for e in events if e.get("evt") == "start"]
        assert len(starts) == 1
        assert starts[0]["query"] == "new query"
        assert starts[0]["mode"] == "chat"

    def test_start_sets_state_busy(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])

        w = CLIWatcher(copilot_dir=copilot)
        w.poll()  # init
        assert w.state == "idle"

        _write_history(hist, ["q2", "q1"])
        _bump_mtime(hist)
        w.poll()
        assert w.state == "busy"

    def test_query_truncated_to_max_len(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["short"])

        w = CLIWatcher(copilot_dir=copilot)
        w.poll()  # init

        long_query = "x" * 200
        _write_history(hist, [long_query, "short"])
        _bump_mtime(hist)

        events = w.poll()
        starts = [e for e in events if e.get("evt") == "start"]
        assert len(starts[0]["query"]) == MAX_QUERY_LEN

    def test_empty_history_array_no_event(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])

        w = CLIWatcher(copilot_dir=copilot)
        w.poll()  # init

        _write_history(hist, [])  # empty array
        _bump_mtime(hist)

        events = w.poll()
        starts = [e for e in events if e.get("evt") == "start"]
        assert len(starts) == 0

    def test_corrupt_json_no_crash(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])

        w = CLIWatcher(copilot_dir=copilot)
        w.poll()  # init

        hist.write_text("{invalid json", encoding="utf-8")
        _bump_mtime(hist)

        events = w.poll()  # should not raise
        assert events == []

    def test_missing_history_file_no_crash(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()

        w = CLIWatcher(copilot_dir=copilot)
        w.poll()  # init
        events = w.poll()
        assert events == []


# ------------------------------------------------------------------
# Turn end detection (events.jsonl quiescence)
# ------------------------------------------------------------------


class TestTurnEnd:
    def test_quiescence_emits_end(self, tmp_path: Path) -> None:
        """After quiescence_sec of silence, an end event is emitted."""
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])
        sess_dir = copilot / "session-state"
        events_file = _touch_events(sess_dir, "s1")

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.1)
        w.poll()  # init

        # Trigger a start event.
        _write_history(hist, ["q2", "q1"])
        _bump_mtime(hist)
        events_file.write_text('{"type":"hook.start"}\n', encoding="utf-8")
        _bump_mtime(events_file)
        start_events = w.poll()
        assert any(e.get("evt") == "start" for e in start_events)

        # Wait for quiescence (> 0.1s).
        time.sleep(0.15)
        end_events = w.poll()
        ends = [e for e in end_events if e.get("evt") == "end"]
        assert len(ends) == 1

    def test_end_sets_state_idle(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.1)
        w.poll()  # init

        _write_history(hist, ["q2", "q1"])
        _bump_mtime(hist)
        w.poll()
        assert w.state == "busy"

        time.sleep(0.15)
        w.poll()
        assert w.state == "idle"

    def test_end_increments_counters(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.1)
        w.poll()  # init
        assert w.queries_today == 0
        assert w.total_queries == 0

        _write_history(hist, ["q2", "q1"])
        _bump_mtime(hist)
        w.poll()

        time.sleep(0.15)
        w.poll()
        assert w.queries_today == 1
        assert w.total_queries == 1

    def test_activity_delays_end(self, tmp_path: Path) -> None:
        """Ongoing events.jsonl writes should keep the turn alive."""
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])
        sess_dir = copilot / "session-state"
        events_file = _touch_events(sess_dir, "s1")

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.2)
        w.poll()  # init

        # Start a turn.
        _write_history(hist, ["q2", "q1"])
        _bump_mtime(hist)
        w.poll()
        assert w.state == "busy"

        # Simulate ongoing activity — keep bumping events.jsonl.
        time.sleep(0.1)
        events_file.write_text('{"type":"tool.start"}\n', encoding="utf-8")
        _bump_mtime(events_file)
        events = w.poll()
        assert not any(e.get("evt") == "end" for e in events)
        assert w.state == "busy"

    def test_no_end_without_start(self, tmp_path: Path) -> None:
        """If no turn was started, quiescence alone doesn't emit end."""
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.1)
        w.poll()  # init

        time.sleep(0.15)
        events = w.poll()
        assert not any(e.get("evt") == "end" for e in events)


# ------------------------------------------------------------------
# Multi-session support
# ------------------------------------------------------------------


class TestMultiSession:
    def test_multiple_sessions_tracked(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])
        sess_dir = copilot / "session-state"
        _touch_events(sess_dir, "session-aaa")
        _touch_events(sess_dir, "session-bbb")

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.1)
        w.poll()  # init

        assert "session-aaa" in w._session_mtimes
        assert "session-bbb" in w._session_mtimes

    def test_any_session_activity_keeps_busy(self, tmp_path: Path) -> None:
        """Activity in ANY session keeps the turn alive."""
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])
        sess_dir = copilot / "session-state"
        _touch_events(sess_dir, "s1")
        ef2 = _touch_events(sess_dir, "s2")

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.2)
        w.poll()  # init

        # Start a turn.
        _write_history(hist, ["q2", "q1"])
        _bump_mtime(hist)
        w.poll()

        # Only session s2 is active.
        time.sleep(0.1)
        ef2.write_text('{"type":"tool.start"}\n', encoding="utf-8")
        _bump_mtime(ef2)
        events = w.poll()
        assert w.state == "busy"
        assert not any(e.get("evt") == "end" for e in events)


# ------------------------------------------------------------------
# Milestones
# ------------------------------------------------------------------


class TestMilestones:
    def test_milestone_at_50(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()
        hist = copilot / "command-history-state.json"
        _write_history(hist, ["q1"])

        w = CLIWatcher(copilot_dir=copilot, quiescence_sec=0.1)
        w.queries_today = 49
        w.total_queries = 49
        w.poll()  # init

        _write_history(hist, ["q2", "q1"])
        _bump_mtime(hist)
        w.poll()

        time.sleep(0.15)
        events = w.poll()
        milestones = [e for e in events if e.get("evt") == "milestone"]
        assert len(milestones) == 1
        assert milestones[0]["n"] == 50


# ------------------------------------------------------------------
# Daily reset
# ------------------------------------------------------------------


class TestDailyReset:
    def test_midnight_rollover(self, tmp_path: Path) -> None:
        copilot = tmp_path / ".copilot"
        copilot.mkdir()

        w = CLIWatcher(copilot_dir=copilot)
        w.queries_today = 10
        w._today = "1999-01-01"

        w.poll()  # triggers reset check
        assert w.queries_today == 0
        assert w._today == date.today().isoformat()
