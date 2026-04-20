"""Short-lived file lock for copilot-buddy hook invocations.

Hook events can fire close together, so state updates and serial writes need a
tiny cross-process critical section. The lock uses atomic file creation and a
short timeout so hooks never block Copilot CLI for long.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Iterator

log = logging.getLogger(__name__)

_LOCK_DIR = os.path.join(os.path.expanduser("~"), ".copilot-buddy")
_LOCK_FILE = os.path.join(_LOCK_DIR, "hook-state.lock")
_LOCK_POLL = 0.01
_LOCK_STALE_AFTER = 10.0


@contextmanager
def hook_lock(timeout: float = 0.3) -> Iterator[bool]:
    """Yield ``True`` when the hook lock was acquired, else ``False``."""
    acquired = _acquire_lock(timeout)
    try:
        yield acquired
    finally:
        if acquired:
            _release_lock()


def _acquire_lock(timeout: float) -> bool:
    """Try to acquire the hook lock within *timeout* seconds."""
    os.makedirs(_LOCK_DIR, exist_ok=True)
    deadline = time.monotonic() + timeout

    while True:
        try:
            fd = os.open(_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
                lock_file.write(f"{os.getpid()} {time.time()}\n")
            return True
        except FileExistsError:
            if _lock_is_stale():
                _remove_stale_lock()
                continue
            if time.monotonic() >= deadline:
                return False
            time.sleep(_LOCK_POLL)
        except OSError as exc:
            log.debug("Hook lock acquisition failed: %s", exc)
            return False


def _lock_is_stale() -> bool:
    """Return ``True`` when the existing lock file is old enough to clear."""
    try:
        age = time.time() - os.path.getmtime(_LOCK_FILE)
    except OSError:
        return False
    return age >= _LOCK_STALE_AFTER


def _remove_stale_lock() -> None:
    """Best-effort removal of a stale lock file."""
    try:
        os.unlink(_LOCK_FILE)
        log.debug("Removed stale hook lock: %s", _LOCK_FILE)
    except OSError:
        pass


def _release_lock() -> None:
    """Best-effort lock release."""
    try:
        os.unlink(_LOCK_FILE)
    except OSError:
        pass
