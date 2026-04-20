"""Tests for the TouchInput gesture detector.

The touch_input module imports CircuitPython-only modules (busio,
adafruit_focaltouch), so we test the gesture logic by constructing a
TouchInput with mocked hardware and driving its update() method.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch




# ── CircuitPython module stubs ──────────────────────────────────
# Inject fake modules before importing touch_input so that module-level
# imports of busio / adafruit_focaltouch / adafruit_bus_device succeed.

_stubs: dict[str, ModuleType] = {}


def _ensure_stubs() -> None:
    """Install stub modules for CircuitPython deps if not present."""
    for name in ("busio", "adafruit_focaltouch", "adafruit_bus_device",
                 "adafruit_bus_device.i2c_device", "micropython"):
        if name not in sys.modules:
            mod = ModuleType(name)
            sys.modules[name] = mod
            _stubs[name] = mod

    # busio.I2C
    busio = sys.modules["busio"]
    if not hasattr(busio, "I2C"):
        busio.I2C = MagicMock  # type: ignore[attr-defined]

    # adafruit_focaltouch.Adafruit_FocalTouch
    ft_mod = sys.modules["adafruit_focaltouch"]
    if not hasattr(ft_mod, "Adafruit_FocalTouch"):
        ft_mod.Adafruit_FocalTouch = MagicMock  # type: ignore[attr-defined]

    # micropython.const
    mp = sys.modules["micropython"]
    if not hasattr(mp, "const"):
        mp.const = lambda x: x  # type: ignore[attr-defined]


_ensure_stubs()

# Now safe to import
from firmware.circuitpython.touch_input import TouchInput  # noqa: E402


# ── Helpers ─────────────────────────────────────────────────────

def _make_touch(config_overrides: dict | None = None):
    """Create a TouchInput with mocked I2C + FocalTouch.

    We patch busio.I2C and Adafruit_FocalTouch so that __init__ succeeds
    without real hardware, then verify the object is enabled.
    """
    config = {
        "touch_i2c_addr": 0x38,
        "touch_sda": MagicMock(),
        "touch_scl": MagicMock(),
        "rotation": 0,
        "width": 240,
        "height": 320,
    }
    if config_overrides:
        config.update(config_overrides)

    mock_ft_instance = MagicMock()
    mock_ft_instance.touches = []

    with patch("firmware.circuitpython.touch_input.busio.I2C"):
        with patch.dict(sys.modules, {"adafruit_focaltouch": MagicMock()}):
            # Re-import so the patched adafruit_focaltouch is used
            ft_mod = sys.modules["adafruit_focaltouch"]
            ft_mod.Adafruit_FocalTouch.return_value = mock_ft_instance
            ti = TouchInput(config)

    assert ti._enabled, "TouchInput should be enabled with valid config"
    return ti


def _set_touches(ti: TouchInput, points: list[dict]) -> None:
    """Configure the mock FocalTouch to return the given touch points."""
    ti._ft.touches = points


# ── Tests ───────────────────────────────────────────────────────

class TestTouchInputInit:
    """Initialization and graceful degradation."""

    def test_no_touch_config(self) -> None:
        """TouchInput is a no-op when touch_i2c_addr is missing."""
        ti = TouchInput({})
        assert not ti._enabled
        assert ti.update(0.0) is None

    def test_missing_sda_scl(self) -> None:
        """TouchInput is a no-op when I2C pins are missing."""
        ti = TouchInput({"touch_i2c_addr": 0x38})
        assert not ti._enabled

    def test_enabled_with_valid_config(self) -> None:
        """TouchInput initializes when all config keys are present."""
        ti = _make_touch()
        assert ti._enabled

    def test_init_failure_graceful(self) -> None:
        """TouchInput degrades gracefully when FocalTouch init raises."""
        config = {
            "touch_i2c_addr": 0x38,
            "touch_sda": MagicMock(),
            "touch_scl": MagicMock(),
        }
        mock_ft_mod = MagicMock()
        mock_ft_mod.Adafruit_FocalTouch.side_effect = RuntimeError("no chip")
        with patch("firmware.circuitpython.touch_input.busio.I2C"):
            with patch.dict(sys.modules, {"adafruit_focaltouch": mock_ft_mod}):
                ti = TouchInput(config)
                assert not ti._enabled
                assert ti.update(1.0) is None


class TestTapGesture:
    """Tap = touch + release within 0.5s and <15px drift."""

    def test_simple_tap(self) -> None:
        """Quick touch and release at the same spot produces short_press."""
        ti = _make_touch()

        # Touch down
        _set_touches(ti, [{"x": 100, "y": 200, "id": 0}])
        assert ti.update(0.0) is None  # touch start, no event yet

        # Release
        _set_touches(ti, [])
        assert ti.update(0.1) == "short_press"

    def test_tap_with_small_drift(self) -> None:
        """Tap with <15px drift still counts as tap."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 100, "y": 200, "id": 0}])
        ti.update(0.0)

        # Move slightly
        _set_touches(ti, [{"x": 110, "y": 205, "id": 0}])
        ti.update(0.1)

        # Release
        _set_touches(ti, [])
        assert ti.update(0.2) == "short_press"

    def test_tap_rejected_too_long(self) -> None:
        """Touch held longer than 0.5s is not a tap."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 100, "y": 200, "id": 0}])
        ti.update(0.0)

        _set_touches(ti, [])
        assert ti.update(0.6) is None  # held too long

    def test_tap_rejected_too_much_drift(self) -> None:
        """Touch with >15px drift is not a tap."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 100, "y": 200, "id": 0}])
        ti.update(0.0)

        # Move far
        _set_touches(ti, [{"x": 140, "y": 200, "id": 0}])
        ti.update(0.1)

        _set_touches(ti, [])
        assert ti.update(0.2) is None  # too much drift


class TestSwipeGesture:
    """Swipe = horizontal movement >50px with directional dominance."""

    def test_horizontal_swipe(self) -> None:
        """Clear horizontal swipe produces long_press immediately."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 50, "y": 150, "id": 0}])
        ti.update(0.0)

        # Move 60px to the right, 0 vertical
        _set_touches(ti, [{"x": 110, "y": 150, "id": 0}])
        result = ti.update(0.1)
        assert result == "long_press"

    def test_swipe_suppresses_tap_on_release(self) -> None:
        """After a swipe fires, release does NOT produce short_press."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 50, "y": 150, "id": 0}])
        ti.update(0.0)

        _set_touches(ti, [{"x": 110, "y": 150, "id": 0}])
        ti.update(0.1)  # fires long_press

        _set_touches(ti, [])
        assert ti.update(0.2) is None  # no tap on release

    def test_swipe_left(self) -> None:
        """Leftward swipe also triggers long_press."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 150, "y": 150, "id": 0}])
        ti.update(0.0)

        _set_touches(ti, [{"x": 90, "y": 150, "id": 0}])
        assert ti.update(0.1) == "long_press"

    def test_diagonal_rejected(self) -> None:
        """Diagonal movement that doesn't pass directional dominance check."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 50, "y": 50, "id": 0}])
        ti.update(0.0)

        # Move 55px horizontal but also 50px vertical — not dominant enough
        _set_touches(ti, [{"x": 105, "y": 100, "id": 0}])
        assert ti.update(0.1) is None  # abs(dx)=55, abs(dy)=50, margin=10 → 55 > 60? no

    def test_vertical_swipe_not_triggered(self) -> None:
        """Vertical movement should not trigger a swipe."""
        ti = _make_touch()

        _set_touches(ti, [{"x": 100, "y": 50, "id": 0}])
        ti.update(0.0)

        _set_touches(ti, [{"x": 100, "y": 120, "id": 0}])
        assert ti.update(0.1) is None


class TestCoordinateMapping:
    """Raw FT6206 → logical coordinate mapping for different rotations."""

    def test_rotation_0(self) -> None:
        ti = _make_touch({"rotation": 0, "width": 240, "height": 320})
        assert ti._map_coords(100, 200) == (100, 200)

    def test_rotation_90(self) -> None:
        ti = _make_touch({"rotation": 90, "width": 240, "height": 320})
        lx, ly = ti._map_coords(100, 200)
        assert lx == 200
        assert ly == 240 - 1 - 100  # 139

    def test_rotation_180(self) -> None:
        ti = _make_touch({"rotation": 180, "width": 240, "height": 320})
        lx, ly = ti._map_coords(100, 200)
        assert lx == 240 - 1 - 100  # 139
        assert ly == 320 - 1 - 200  # 119

    def test_rotation_270(self) -> None:
        ti = _make_touch({"rotation": 270, "width": 240, "height": 320})
        lx, ly = ti._map_coords(100, 200)
        assert lx == 320 - 1 - 200  # 119
        assert ly == 100


class TestIsPressedProperty:
    """is_pressed property tracking."""

    def test_not_pressed_initially(self) -> None:
        ti = _make_touch()
        assert not ti.is_pressed

    def test_pressed_during_touch(self) -> None:
        ti = _make_touch()
        _set_touches(ti, [{"x": 100, "y": 100, "id": 0}])
        ti.update(0.0)
        assert ti.is_pressed

    def test_not_pressed_after_release(self) -> None:
        ti = _make_touch()
        _set_touches(ti, [{"x": 100, "y": 100, "id": 0}])
        ti.update(0.0)
        _set_touches(ti, [])
        ti.update(0.1)
        assert not ti.is_pressed


class TestOSErrorHandling:
    """I2C read errors should be handled gracefully."""

    def test_oserror_during_read(self) -> None:
        """OSError from touch read should return None, not crash."""
        ti = _make_touch()
        # Replace .touches with a property that raises OSError
        mock_ft = MagicMock()
        type(mock_ft).touches = property(lambda self: (_ for _ in ()).throw(OSError("I2C")))
        ti._ft = mock_ft
        assert ti.update(0.0) is None
