"""Tests for bridge transports — LoopbackTransport and SerialTransport."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from bridge.transport_loopback import LoopbackTransport
from bridge.transport_serial import SerialTransport


# ------------------------------------------------------------------
# LoopbackTransport
# ------------------------------------------------------------------


def test_loopback_connect() -> None:
    transport = LoopbackTransport()
    assert transport.connect() is True
    assert transport.connected is True


def test_loopback_send_captures() -> None:
    transport = LoopbackTransport()
    transport.connect()
    transport.send('{"cmd":"heartbeat"}\n')
    transport.send('{"cmd":"event"}\n')
    assert len(transport.sent_messages) == 2
    assert transport.sent_messages[0] == '{"cmd":"heartbeat"}\n'


def test_loopback_receive_injects() -> None:
    transport = LoopbackTransport()
    transport.connect()
    transport.inject_responses.append('{"ack":"ok"}')
    result = transport.receive()
    assert result == '{"ack":"ok"}'
    # Queue is now empty.
    assert transport.receive() is None


# ------------------------------------------------------------------
# SerialTransport — mocked serial
# ------------------------------------------------------------------


@patch("bridge.transport_serial.serial.Serial")
def test_serial_connect_success(mock_serial_cls: MagicMock) -> None:
    mock_port = MagicMock()
    mock_serial_cls.return_value = mock_port

    transport = SerialTransport(port="COM3")
    result = transport.connect()

    assert result is True
    mock_serial_cls.assert_called_once_with(
        port="COM3",
        baudrate=115200,
        timeout=5.0,
        write_timeout=5.0,
    )


@patch("bridge.transport_serial.serial.Serial")
def test_serial_connect_failure(mock_serial_cls: MagicMock) -> None:
    import serial

    mock_serial_cls.side_effect = serial.SerialException("port busy")

    transport = SerialTransport(port="COM99")
    result = transport.connect()

    assert result is False
    assert transport.connected is False


@patch("bridge.transport_serial.serial.Serial")
def test_serial_send(mock_serial_cls: MagicMock) -> None:
    mock_port = MagicMock()
    mock_port.is_open = True
    mock_serial_cls.return_value = mock_port

    transport = SerialTransport(port="COM3")
    transport.connect()
    ok = transport.send('{"cmd":"heartbeat"}\n')

    assert ok is True
    mock_port.write.assert_called_once_with(b'{"cmd":"heartbeat"}\n')
    mock_port.flush.assert_called_once()


@patch("bridge.transport_serial.serial.Serial")
def test_serial_send_after_disconnect_attempts_reconnect(
    mock_serial_cls: MagicMock,
) -> None:
    mock_port = MagicMock()
    mock_port.is_open = True
    mock_serial_cls.return_value = mock_port

    transport = SerialTransport(port="COM3")
    # Do NOT call connect() — simulate a disconnected state.
    # The transport should try to reconnect when send() is called.
    transport._last_reconnect_attempt = 0.0  # allow immediate reconnect
    ok = transport.send('{"cmd":"test"}\n')

    assert ok is True
    # connect() was called internally (Serial constructor invoked).
    assert mock_serial_cls.call_count >= 1


@patch("bridge.transport_serial.serial.tools.list_ports.comports")
@patch("bridge.transport_serial.serial.Serial")
def test_auto_detect_finds_device(
    mock_serial_cls: MagicMock,
    mock_comports: MagicMock,
) -> None:
    port_info = MagicMock()
    port_info.device = "COM5"
    mock_comports.return_value = [port_info]

    # The context-manager Serial probe must return a valid status response.
    mock_probe = MagicMock()
    mock_probe.readline.return_value = b'{"ack":"status"}\n'
    mock_probe.__enter__ = MagicMock(return_value=mock_probe)
    mock_probe.__exit__ = MagicMock(return_value=False)
    mock_serial_cls.return_value = mock_probe

    transport = SerialTransport()
    result = transport.auto_detect_port()

    assert result == "COM5"


@patch("bridge.transport_serial.serial.tools.list_ports.comports")
def test_auto_detect_no_devices(mock_comports: MagicMock) -> None:
    mock_comports.return_value = []

    transport = SerialTransport()
    result = transport.auto_detect_port()

    assert result is None
