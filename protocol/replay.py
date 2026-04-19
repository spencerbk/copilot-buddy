"""Replay fixture files over serial or stdout.

Reads a newline-delimited JSON fixture file and sends each line to a
serial port (for driving an ESP32-S3 desk pet) or to stdout (for testing).

Usage:
    python replay.py fixtures/full_session.jsonl
    python replay.py fixtures/full_session.jsonl --port COM3
    python replay.py fixtures/full_session.jsonl --port COM3 --baud 115200
    python replay.py fixtures/full_session.jsonl --delay 2
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def send_lines(
    path: Path,
    *,
    port: str | None = None,
    baud: int = 115200,
    delay: float = 0.5,
) -> None:
    """Read *path* line-by-line and send each line to *port* (or stdout)."""

    lines = path.read_text(encoding="utf-8").splitlines()

    if port is not None:
        try:
            import serial  # type: ignore[import-untyped]
        except ImportError:
            print(
                "error: pyserial is required for serial output "
                "(pip install pyserial)",
                file=sys.stderr,
            )
            sys.exit(1)

        ser = serial.Serial(port, baudrate=baud, timeout=1)
        print(f"Opened {port} at {baud} baud", file=sys.stderr)

        try:
            for i, line in enumerate(lines, 1):
                ser.write((line + "\n").encode("utf-8"))
                print(f"[{i}/{len(lines)}] → {line}", file=sys.stderr)
                if i < len(lines):
                    time.sleep(delay)
        finally:
            ser.close()
            print("Serial port closed", file=sys.stderr)
    else:
        for i, line in enumerate(lines, 1):
            print(line, flush=True)
            if i < len(lines):
                time.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay a .jsonl fixture file over serial or stdout.",
    )
    parser.add_argument(
        "fixture",
        type=Path,
        help="Path to a .jsonl fixture file",
    )
    parser.add_argument(
        "--port",
        default=None,
        help="Serial port (e.g. COM3, /dev/ttyACM0). Omit for stdout.",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds between lines (default: 0.5)",
    )
    args = parser.parse_args()

    if not args.fixture.is_file():
        print(f"error: file not found: {args.fixture}", file=sys.stderr)
        sys.exit(1)

    try:
        send_lines(args.fixture, port=args.port, baud=args.baud, delay=args.delay)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
