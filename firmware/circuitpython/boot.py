"""
boot.py — USB CDC configuration for copilot-buddy.

Enables the secondary USB CDC data serial port (usb_cdc.data) so the
host bridge can send JSON events to the device while the REPL console
remains available for debugging.

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

import usb_cdc

usb_cdc.enable(console=True, data=True)
