"""Tests for bridge.watcher — Copilot CLI process scanning and polling."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from bridge.watcher import CopilotWatcher, extract_query, scan_processes


# ------------------------------------------------------------------
# extract_query
# ------------------------------------------------------------------


def test_extract_query_basic() -> None:
    result = extract_query(["gh", "copilot", "suggest", "hello world"])
    assert result == "hello world"


def test_extract_query_with_flags() -> None:
    # -t is a flag that takes a value; extract_query should skip both
    # the flag and its argument, returning the actual query text.
    result = extract_query(["gh", "copilot", "suggest", "-t", "shell", "list files"])
    assert result == "list files"


def test_extract_query_target_flag_short() -> None:
    """``-t shell`` should be skipped, returning the real query."""
    result = extract_query(
        ["gh", "copilot", "suggest", "-t", "shell", "how to list files"]
    )
    assert result == "how to list files"


def test_extract_query_target_flag_long() -> None:
    """``--target shell`` should be skipped, returning the real query."""
    result = extract_query(
        ["gh", "copilot", "explain", "--target", "shell", "what is grep"]
    )
    assert result == "what is grep"


def test_extract_query_missing() -> None:
    result = extract_query(["gh", "copilot", "suggest"])
    assert result == ""


def test_extract_query_truncation() -> None:
    long_query = "x" * 200
    result = extract_query(["gh", "copilot", "suggest", long_query])
    assert len(result) == 80
    assert result == long_query[:80]


# ------------------------------------------------------------------
# scan_processes
# ------------------------------------------------------------------


def _make_proc(pid: int, name: str, cmdline: list[str] | None) -> MagicMock:
    """Build a fake psutil process with the given info dict."""
    proc = MagicMock()
    proc.info = {"pid": pid, "name": name, "cmdline": cmdline}
    return proc


@patch("bridge.watcher.psutil.process_iter")
def test_scan_finds_copilot_suggest_process(mock_iter: MagicMock) -> None:
    mock_iter.return_value = [
        _make_proc(100, "gh", ["gh", "copilot", "suggest", "how to sort a list"]),
    ]
    results = scan_processes()
    assert len(results) == 1
    assert results[0]["pid"] == 100
    assert results[0]["mode"] == "suggest"
    assert results[0]["query"] == "how to sort a list"


@patch("bridge.watcher.psutil.process_iter")
def test_scan_finds_copilot_explain_process(mock_iter: MagicMock) -> None:
    mock_iter.return_value = [
        _make_proc(200, "gh", ["gh", "copilot", "explain", "what is a mutex"]),
    ]
    results = scan_processes()
    assert len(results) == 1
    assert results[0]["mode"] == "explain"


@patch("bridge.watcher.psutil.process_iter")
def test_scan_ignores_unrelated_process(mock_iter: MagicMock) -> None:
    mock_iter.return_value = [
        _make_proc(300, "python", ["python", "script.py"]),
    ]
    results = scan_processes()
    assert results == []


@patch("bridge.watcher.psutil.process_iter")
def test_scan_handles_none_cmdline(mock_iter: MagicMock) -> None:
    mock_iter.return_value = [_make_proc(400, "system", None)]
    results = scan_processes()
    assert results == []


@patch("bridge.watcher.psutil.process_iter")
def test_scan_handles_access_denied(mock_iter: MagicMock) -> None:
    import psutil

    bad_proc = MagicMock()
    bad_proc.info.__getitem__ = MagicMock(side_effect=psutil.AccessDenied(500))
    bad_proc.info.get = MagicMock(side_effect=psutil.AccessDenied(500))
    mock_iter.return_value = [bad_proc]
    # Should not raise
    results = scan_processes()
    assert results == []


# ------------------------------------------------------------------
# CopilotWatcher.poll
# ------------------------------------------------------------------


@patch("bridge.watcher.scan_processes")
def test_poll_detects_new_process(mock_scan: MagicMock) -> None:
    mock_scan.return_value = [
        {"pid": 1000, "mode": "suggest", "query": "hello"},
    ]
    watcher = CopilotWatcher()
    events = watcher.poll()

    start_events = [e for e in events if e.get("evt") == "start"]
    assert len(start_events) == 1
    assert start_events[0]["query"] == "hello"
    assert start_events[0]["mode"] == "suggest"


@patch("bridge.watcher.scan_processes")
def test_poll_detects_ended_process(mock_scan: MagicMock) -> None:
    watcher = CopilotWatcher()

    # First poll: process appears.
    mock_scan.return_value = [{"pid": 2000, "mode": "suggest", "query": "q"}]
    watcher.poll()
    assert watcher.queries_today == 0

    # Second poll: process gone.
    mock_scan.return_value = []
    events = watcher.poll()

    end_events = [e for e in events if e.get("evt") == "end"]
    assert len(end_events) == 1
    assert watcher.queries_today == 1


@patch("bridge.watcher.scan_processes")
def test_poll_milestone_every_50(mock_scan: MagicMock) -> None:
    watcher = CopilotWatcher()
    # Pre-seed the counter to 49 so the next ended query triggers milestone.
    watcher.queries_today = 49
    watcher.total_queries = 49

    # Appear then disappear — that's one completed query → total 50.
    mock_scan.return_value = [{"pid": 3000, "mode": "suggest", "query": "q"}]
    watcher.poll()
    mock_scan.return_value = []
    events = watcher.poll()

    milestone_events = [e for e in events if e.get("evt") == "milestone"]
    assert len(milestone_events) == 1
    assert milestone_events[0]["n"] == 50


@patch("bridge.watcher.scan_processes")
def test_poll_midnight_reset(mock_scan: MagicMock) -> None:
    mock_scan.return_value = []
    watcher = CopilotWatcher()
    watcher.queries_today = 10

    # Simulate a date change by backdating the internal tracker.
    watcher._today = "1999-01-01"
    watcher.poll()
    assert watcher.queries_today == 0
    assert watcher._today == date.today().isoformat()
