---
name: circuitpython-code-review
description: Review CircuitPython changes for correctness, hardware safety, Adafruit conventions, and security issues. Produces severity-ranked findings and a go/no-go verdict.
---

# CircuitPython Code Review

Use this skill when the goal is to review CircuitPython code changes for correctness and merge-readiness.

## Focus areas

- **Correctness** — logic errors, off-by-one, wrong return values, unhandled states.
- **Hardware safety** — pin conflicts, peripheral state management, interrupt handling, timing issues.
- **Adafruit conventions** — proper use of Adafruit libraries, `board` pin names, `adafruit_bus_device` patterns.
- **Memory efficiency** — heap allocation pressure, buffer reuse, gc pressure, CIRCUITPY storage usage.
- **Error handling** — silent failures, unhandled hardware exceptions, missing timeouts.
- **Security** — hardcoded credentials, unvalidated external input, unsafe network operations.

## Required outcomes

The task is not complete until:
- the diff or scope has been reviewed
- findings are ordered by severity (BLOCKER / MAJOR / MINOR / NIT)
- a verdict is stated: NO-GO, GO WITH FIXES, or GO

## Workflow

1. Identify the diff or requested review scope.
2. Read the changed files and immediate context.
3. Check each focus area, with special attention to Adafruit library usage patterns.
4. Check Ruff and Pyright implications in touched scope.
5. Produce findings ordered by severity.
6. State the approval verdict.

## Decision rules

- Only surface issues that genuinely matter — no style nitpicks unless they affect correctness.
- BLOCKER = will cause runtime failure, data loss, hardware damage, or security vulnerability.
- MAJOR = likely bug, significant memory waste, or incorrect Adafruit library usage.
- MINOR = improvement opportunity, non-critical but worth fixing.
- NIT = cosmetic or preference; mention only if few other findings exist.
- Do NOT modify code — this skill is read-only review.
