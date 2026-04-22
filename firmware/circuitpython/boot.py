"""
boot.py — USB CDC configuration for copilot-buddy.

Enables the secondary USB CDC data serial port (usb_cdc.data) so the
host bridge can send JSON events to the device while the REPL console
remains available for debugging.

The ESP32-S2 has a limited USB endpoint budget.  Disabling the default
USB HID, MIDI, and mass-storage devices (which copilot-buddy does not
use at runtime) frees the endpoints needed for the second CDC channel.

To copy files after this is active, hold BOOT during reset to enter
safe mode — the CIRCUITPY drive will reappear.

IMPORTANT:
- This file runs ONCE on hard reset (not on soft reload / Ctrl+D).
- After copying this file to CIRCUITPY, you MUST hard-reset the board
  (press the reset button or power cycle).
- The board will then appear as TWO serial ports:
  1. Console/REPL (for debugging)
  2. Data port (for bridge communication)
- If something goes wrong, hold BOOT during reset to enter safe mode,
  then delete or rename boot.py from the CIRCUITPY drive.
"""

import storage
import usb_cdc
import usb_hid
import usb_midi

# Free USB endpoints by disabling devices copilot-buddy doesn't need
usb_hid.disable()
usb_midi.disable()
storage.disable_usb_drive()

usb_cdc.enable(console=True, data=True)
