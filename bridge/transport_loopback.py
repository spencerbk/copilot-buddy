"""Loopback transport for testing the bridge without hardware."""

from __future__ import annotations


class LoopbackTransport:
    """In-memory transport that records sent messages.

    Drop-in replacement for :class:`~transport_serial.SerialTransport`
    when running tests or demos without a real ESP32.
    """

    def __init__(self) -> None:
        self.sent_messages: list[str] = []
        self.inject_responses: list[str] = []
        self._connected: bool = False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Always succeeds."""
        self._connected = True
        return True

    def disconnect(self) -> None:
        """No-op — nothing to close."""
        self._connected = False

    # ------------------------------------------------------------------
    # Data I/O
    # ------------------------------------------------------------------

    def send(self, data: str) -> bool:
        """Record *data* in :attr:`sent_messages`."""
        self.sent_messages.append(data)
        return True

    def receive(self, timeout: float = 0.1) -> str | None:
        """Pop the next pre-loaded response, or ``None``."""
        if self.inject_responses:
            return self.inject_responses.pop(0)
        return None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:  # noqa: D401
        """Always ``True`` after :meth:`connect`."""
        return self._connected
