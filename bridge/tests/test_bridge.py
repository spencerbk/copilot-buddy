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
