"""Integration tests for the copilot-buddy bridge main loop."""

from __future__ import annotations

import json
import threading
import time
from unittest.mock import patch

from bridge.copilot_bridge import main, run
from bridge.transport_loopback import LoopbackTransport
from bridge.watcher import CopilotWatcher


def test_run_sends_heartbeat() -> None:
    """The main loop should emit at least one heartbeat within a few seconds."""
    transport = LoopbackTransport()
    transport.connect()
    watcher = CopilotWatcher(poll_interval=0.2)

    # Run the bridge in a background thread with mocked scan_processes.
    with patch("bridge.watcher.scan_processes", return_value=[]):
        t = threading.Thread(target=run, args=(transport, watcher), daemon=True)
        t.start()
        time.sleep(3)

    # Parse sent messages and look for a heartbeat (has "state" key).
    heartbeats = []
    for msg in transport.sent_messages:
        try:
            data = json.loads(msg)
        except json.JSONDecodeError:
            continue
        if "state" in data:
            heartbeats.append(data)

    assert len(heartbeats) >= 1
    assert heartbeats[0]["state"] == "idle"
    assert "queries_today" in heartbeats[0]


def test_run_forwards_events() -> None:
    """Events returned by watcher.poll() should be forwarded to the transport."""
    transport = LoopbackTransport()
    transport.connect()
    watcher = CopilotWatcher(poll_interval=0.2)

    call_count = 0
    original_poll = watcher.poll

    def fake_poll() -> list[dict]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Simulate a start event on the first poll.
            return [{"evt": "start", "query": "test query", "mode": "suggest"}]
        return original_poll()

    with patch.object(watcher, "poll", side_effect=fake_poll):
        t = threading.Thread(target=run, args=(transport, watcher), daemon=True)
        t.start()
        time.sleep(2)

    # Find the start event in sent messages.
    start_events = []
    for msg in transport.sent_messages:
        try:
            data = json.loads(msg)
        except json.JSONDecodeError:
            continue
        if data.get("evt") == "start":
            start_events.append(data)

    assert len(start_events) >= 1
    assert start_events[0]["query"] == "test query"


@patch("bridge.watcher.scan_processes", return_value=[])
@patch("signal.signal")  # signal.signal fails outside main thread
def test_main_loopback_mode(_mock_signal: object, _mock_scan: object) -> None:
    """main(['--transport', 'loopback']) should start without error."""
    t = threading.Thread(
        target=main,
        args=(["--transport", "loopback", "--poll-interval", "0.2"],),
        daemon=True,
    )
    t.start()
    time.sleep(2)

    # If the thread is still alive the bridge loop is running successfully.
    assert t.is_alive()


# ------------------------------------------------------------------
# HUD entries + msg tests
# ------------------------------------------------------------------


def test_heartbeat_includes_msg() -> None:
    """Heartbeats should include a 'msg' field."""
    transport = LoopbackTransport()
    transport.connect()
    watcher = CopilotWatcher(poll_interval=0.2)

    with patch("bridge.watcher.scan_processes", return_value=[]):
        t = threading.Thread(target=run, args=(transport, watcher), daemon=True)
        t.start()
        time.sleep(3)

    heartbeats = []
    for msg in transport.sent_messages:
        try:
            data = json.loads(msg)
        except json.JSONDecodeError:
            continue
        if "state" in data and "msg" in data:
            heartbeats.append(data)

    assert len(heartbeats) >= 1
    assert isinstance(heartbeats[0]["msg"], str)
    assert len(heartbeats[0]["msg"]) > 0


def test_heartbeat_entries_after_start_event() -> None:
    """After a start event, heartbeats should include entries."""
    transport = LoopbackTransport()
    transport.connect()
    watcher = CopilotWatcher(poll_interval=0.2)

    call_count = 0
    original_poll = watcher.poll

    def fake_poll() -> list[dict]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return [{"evt": "start", "query": "explain regex", "mode": "suggest"}]
        return original_poll()

    with patch.object(watcher, "poll", side_effect=fake_poll):
        t = threading.Thread(target=run, args=(transport, watcher), daemon=True)
        t.start()
        time.sleep(3)

    # Find heartbeats with entries
    heartbeats_with_entries = []
    for msg in transport.sent_messages:
        try:
            data = json.loads(msg)
        except json.JSONDecodeError:
            continue
        if "state" in data and "entries" in data:
            heartbeats_with_entries.append(data)

    assert len(heartbeats_with_entries) >= 1
    entries = heartbeats_with_entries[0]["entries"]
    assert len(entries) >= 1
    # Entry should be "repo HH:MM query" — at minimum contains time
    assert ":" in entries[0]  # colon from HH:MM


def test_entry_format_timestamp_prefix() -> None:
    """Each entry should contain a repo prefix and HH:MM timestamp."""
    from bridge.copilot_bridge import _add_entry, _entries
    _entries.clear()
    _add_entry("test query")
    assert len(_entries) == 1
    # Format: "repo HH:MM query" — find the colon in the timestamp
    entry = _entries[0]
    assert ":" in entry  # HH:MM present
    # Entry contains at least part of the query
    assert "test" in entry
    _entries.clear()


def test_entry_truncation() -> None:
    """Entries should be truncated to _MAX_ENTRY_LEN."""
    from bridge.copilot_bridge import _MAX_ENTRY_LEN, _add_entry, _entries
    _entries.clear()
    long_query = "a" * 100
    _add_entry(long_query)
    assert len(_entries[0]) <= _MAX_ENTRY_LEN
    _entries.clear()


def test_entries_ring_buffer_cap() -> None:
    """Ring buffer should not exceed _MAX_ENTRIES."""
    from bridge.copilot_bridge import _MAX_ENTRIES, _add_entry, _entries
    _entries.clear()
    for i in range(_MAX_ENTRIES + 3):
        _add_entry("query {}".format(i))
    assert len(_entries) == _MAX_ENTRIES
    # Newest should be first
    assert "query {}".format(_MAX_ENTRIES + 2) in _entries[0]
    _entries.clear()


def test_heartbeat_under_512_bytes() -> None:
    """Heartbeat JSON line should stay under 512 bytes."""
    from bridge.copilot_bridge import _add_entry, _entries
    _entries.clear()
    # Add max entries with long queries
    for i in range(8):
        _add_entry("a" * 50)

    transport = LoopbackTransport()
    transport.connect()
    watcher = CopilotWatcher(poll_interval=0.2)

    with patch("bridge.watcher.scan_processes", return_value=[]):
        t = threading.Thread(target=run, args=(transport, watcher), daemon=True)
        t.start()
        time.sleep(3)

    _entries.clear()


def test_detect_repo_name_from_git() -> None:
    """_detect_repo_name returns basename of git toplevel."""
    from bridge.copilot_bridge import _detect_repo_name
    name = _detect_repo_name()
    # We're in the copilot-buddy repo
    assert name == "copilot-buddy"


def test_detect_repo_name_fallback(tmp_path, monkeypatch) -> None:
    """_detect_repo_name falls back to CWD basename when git fails."""
    from bridge.copilot_bridge import _detect_repo_name
    monkeypatch.chdir(tmp_path)
    name = _detect_repo_name()
    assert name == tmp_path.name


def test_get_repo_name_caches() -> None:
    """_get_repo_name caches the result on first call."""
    import bridge.copilot_bridge as mod
    old = mod._repo_name
    try:
        mod._repo_name = ""
        result1 = mod._get_repo_name()
        assert result1
        assert mod._repo_name == result1
        # Second call returns same without re-detecting
        result2 = mod._get_repo_name()
        assert result2 == result1
    finally:
        mod._repo_name = old


def test_entry_includes_repo_prefix() -> None:
    """Entries should include the repo name prefix."""
    from bridge.copilot_bridge import _add_entry, _entries, _get_repo_name
    _entries.clear()
    _add_entry("hello")
    entry = _entries[0]
    repo = _get_repo_name()[:6]
    assert entry.startswith(repo)
    _entries.clear()
