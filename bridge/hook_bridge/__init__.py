"""copilot-buddy hook bridge — event-driven alternative to the polling daemon.

Invoked by Copilot CLI hooks. Each hook event triggers a short-lived process
that translates the event to copilot-buddy's JSON protocol and sends it to
the ESP32 over USB serial. No long-running daemon required.
"""
