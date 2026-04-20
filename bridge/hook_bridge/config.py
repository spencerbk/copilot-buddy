"""Configuration for the copilot-buddy hook bridge.

Resolution order: environment variable > config file > built-in default.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# Defaults
DEFAULT_BAUD = 115200
DEFAULT_SERIAL_TIMEOUT = 0.3
CONFIG_FILENAME = ".copilot-buddy.local.json"

# USB description patterns used for auto-detection
DEFAULT_DEVICE_DESCRIPTIONS: list[str] = [
    "CircuitPython",
    "copilot-buddy",
    "ESP32",
    "USB Serial",
]


@dataclass
class HookConfig:
    """Resolved configuration for a single hook invocation."""

    serial_port: str | None = None
    baud: int = DEFAULT_BAUD
    serial_timeout: float = DEFAULT_SERIAL_TIMEOUT
    dry_run: bool = False
    device_match_descriptions: list[str] = field(
        default_factory=lambda: list(DEFAULT_DEVICE_DESCRIPTIONS)
    )


def _find_config_file(start_dir: str | None = None) -> str | None:
    """Walk from *start_dir* upward looking for the config file."""
    current = os.path.abspath(start_dir or os.getcwd())
    while True:
        candidate = os.path.join(current, CONFIG_FILENAME)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def _load_file(path: str) -> dict:
    """Read and parse a JSON config file.  Returns ``{}`` on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        log.debug("Config file %s unreadable: %s", path, exc)
    return {}


def load_config(config_dir: str | None = None) -> HookConfig:
    """Build a :class:`HookConfig` by merging file, env, and defaults."""
    cfg = HookConfig()

    # --- config file layer ---
    path = _find_config_file(config_dir)
    if path is not None:
        data = _load_file(path)
        if "serial_port" in data:
            cfg.serial_port = str(data["serial_port"])
        if "baud" in data:
            try:
                cfg.baud = int(data["baud"])
            except (TypeError, ValueError):
                pass
        match = data.get("device_match")
        if isinstance(match, dict):
            descs = match.get("description_contains")
            if isinstance(descs, list):
                cfg.device_match_descriptions = [str(d) for d in descs]

    # --- environment layer (overrides file) ---
    env_port = os.environ.get("COPILOT_BUDDY_PORT")
    if env_port:
        cfg.serial_port = env_port

    env_baud = os.environ.get("COPILOT_BUDDY_BAUD")
    if env_baud:
        try:
            cfg.baud = int(env_baud)
        except ValueError:
            pass

    env_dry = os.environ.get("COPILOT_BUDDY_DRY_RUN", "").lower()
    if env_dry in ("1", "true", "yes"):
        cfg.dry_run = True

    return cfg
