---
name: circuitpython-bugfix
description: Diagnose and fix a CircuitPython bug from an error, crash, or unexpected hardware behavior. Follows Adafruit conventions. Uses static analysis only (Ruff + Pyright) — no pytest.
---

# CircuitPython Bugfix

Use this skill when the goal is to diagnose and fix a bug in CircuitPython code.

Typical triggers:
- error message or traceback from REPL or serial console
- unexpected hardware behavior (sensor readings, display output, NeoPixel patterns)
- boot failure or import error on CIRCUITPY drive
- storage pressure or memory allocation failure
- silent failure in I2C/SPI communication with Adafruit breakouts
- a code review that asks you to find or fix bugs

## Required outcomes

The task is not complete until all of the following are true:
- the failure signal has been investigated
- the root cause has been identified and stated plainly
- the smallest correct fix has been implemented following Adafruit conventions
- the fix does not introduce new Ruff or Pyright errors
- no unrelated code was changed

## Iron law

No fixes without root cause investigation first. If you have not completed steps 1-3, you cannot propose a fix.

## Workflow

1. Inspect the failure signal.
   - Error message, serial output, unexpected hardware behavior, or boot failure.
   - Identify Adafruit library dependencies and hardware connections.

   **Review-triggered investigations:** When the task asks you to review code
   for correctness or regressions, do NOT just inspect the serial output and stop
   if nothing looks wrong. The existing checks may not cover the regression. Instead:
   - Read the code that was "refactored" or "simplified" and ask: what safety
     checks, guards, or conditions might have been removed?
   - Look for removed resource-management guards: gc.collect() calls, CIRCUITPY
     drive space checks, board pin de-init, interrupt disable/enable pairs.
   - If you find a missing check, add it.

2. Reproduce or localize the failure.
   - Trace the code path from `code.py` (or the project entry point) to the failure.
   - Check pin conflicts, CIRCUITPY storage pressure, and Adafruit driver initialization patterns.
   - Check `board` pin assignments and I2C/SPI bus configuration.

3. Isolate the root cause.
   - Trace from the observed failure to the concrete defect.
   - Trace data flow backward: where does the bad value originate? What called this with the bad value? Keep tracing until you find the source. Fix at source, not at symptom.
   - Find working examples of similar code in the same codebase. Compare -- what is different between working and broken?
   - Check CircuitPython-specific traps: CIRCUITPY drive space exhaustion, gc.collect() placement, board pin conflicts, Adafruit library version mismatches, import order for board-specific modules.
   - State the likely root cause plainly.

4. Form competing hypotheses before attempting any fix.
   - List at least 3 plausible root causes — do not commit to the first explanation that seems reasonable.
   - For each hypothesis, note the specific evidence that supports it and the evidence that would disprove it.
   - Rank hypotheses by likelihood and testability.
   - Verify the most likely hypothesis first with the smallest possible test (add a print/log, check a value, run a targeted command).
   - If the first hypothesis is disproved, move to the next — do not stack speculative fixes.
   - If 3+ hypotheses are disproved, stop and re-examine your assumptions about the failure. Discuss with the user before attempting more fixes.

5. Implement the smallest correct fix.
   - Follow Adafruit library conventions and driver patterns.
   - Use `adafruit_bus_device` for I2C/SPI abstractions where appropriate.
   - Prefer `board` module pin names over raw GPIO numbers.

6. Validate with static analysis.
   - Run Ruff on changed files.
   - Run Pyright on changed files.
   - Do NOT use pytest — CircuitPython projects use static analysis only.

7. Report the result.
   Include: failure summary, root cause, files changed, validation results.

8. RCA summary.
   After reporting, produce a brief root cause analysis for use by the **bugfix-rca** skill:
   - **Root cause category**: classify as one of: logic error, missing validation, edge case not covered, data shape/type mismatch, concurrency/timing, configuration/environment, dependency issue, missing test coverage, error handling gap, or API contract violation.
   - **Detection gap**: what test, lint rule, type annotation, or review practice could have caught this earlier?
   - **Prevention recommendations**: 1-3 specific, actionable measures (e.g., "add a boundary-value test for X", "enable lint rule Y", "add type annotation on Z").


9. **RCA and prevention.**
    After the fix is validated, follow the **bugfix-rca** skill to analyze prevention gaps, implement preventive measures, and store the lesson learned.

## Red flags -- stop and return to step 3

If you catch yourself thinking any of these, you are guessing instead of investigating:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "It is probably X, let me fix that"
- "I do not fully understand but this might work"
- "Add multiple changes, run tests"
- "One more fix attempt" (when 2+ have already failed)
- Proposing solutions before tracing data flow

## Decision rules

- Fix the code rather than weakening a correct test.
- If the failure is caused by an outdated test and behavior intentionally changed, update the test and state that clearly.
- If the failure appears pre-existing and unrelated to the requested fix, say so explicitly and keep the current scope narrow.
- Prefer repository tooling and existing patterns over ad hoc commands or new abstractions.
- Fix the root cause, not the symptom.
- Follow Adafruit library patterns for driver initialization and error handling.
- If the bug is in an Adafruit library usage pattern, suggest the correct pattern.
- Keep fixes memory-efficient.
- If the fix requires a new Adafruit library, note the dependency clearly.
