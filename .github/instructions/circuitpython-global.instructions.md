---
name: "Global CircuitPython defaults"
description: "Default instructions for CircuitPython work across my projects"
applyTo: "**/*.py"
---

# CircuitPython Global Instructions

## Runtime constraints

- This is CircuitPython, not CPython. Do not suggest standard Python features, libraries, or patterns that are unavailable.
- Be mindful of constrained RAM, storage, CPU, and peripheral limitations.
- Prefer simple, robust approaches suitable for microcontrollers.
- Avoid unnecessary allocations, closures, and heavyweight abstractions.
- Prefer pre-allocated buffers over repeated allocations in hot paths.
- Avoid importing modules that are not available or are too large for the target board.

## Adafruit conventions

- Follow Adafruit library conventions for driver and helper code.
- Use `adafruit_bus_device` for I2C and SPI abstractions when writing device drivers.
- Prefer Adafruit libraries (`adafruit_neopixel`, `adafruit_display_text`, `adafruit_requests`, etc.) when they cover the use case.
- Use `board` module pin names rather than raw GPIO numbers when available.
- Structure projects with `code.py` as the entry point unless the project uses a different convention.

## Code style

- Prefer clear, direct, maintainable code over cleverness.
- Prefer explicit names over short or cryptic names.
- Add comments for hardware-specific logic, pin assignments, timing constraints, and non-obvious intent.
- Do not add redundant comments that merely restate the code.
- Keep files small and focused; microcontrollers benefit from smaller import graphs.

## Hardware awareness

- Document pin assignments and peripheral configurations clearly.
- Be explicit about I2C, SPI, UART bus numbers, frequencies, and pin mappings.
- Include timing considerations for sensors, displays, and communication protocols.
- Handle hardware initialization failures gracefully — peripherals may not always be connected.
- Prefer `try`/`except` around hardware operations that can fail at runtime.

## Error handling

- Fail clearly and predictably.
- Do not swallow exceptions silently.
- Include useful error messages, but keep them concise — print output is often the only diagnostic channel.
- For long-running loops, consider supervisor.reload() and recovery strategies.

## Validation

- Static analysis only: use Ruff for linting and Pyright for type checking.
- Do not introduce pytest or other CPython test frameworks.
- Validate changes through static analysis and manual hardware testing.

## Dependencies

- Prefer built-in CircuitPython modules and Adafruit libraries.
- Use the Adafruit CircuitPython Bundle for community libraries.
- Do not add dependencies without clear justification.

## Git operations

- Do not run `git commit` or `git push` unless the user explicitly asks you to commit and/or push.
- Do not merge pull requests (via `gh pr merge`, `git merge`, or any equivalent) unless the user explicitly asks you to merge. Opening a PR does not imply permission to merge it.
- Making code changes does not imply permission to commit or push them.
- Do not resolve merge conflicts by replacing the entire file with one side's version. This includes `git checkout --theirs`, `git checkout --ours`, and any whole-file side selection — these silently discard the other side's changes.
- When resolving merge conflicts:
  - Show the conflicting hunks from both branches so the user can see what would be kept and what would be lost.
  - For additive files (`.gitignore`, `requirements.txt`, config files, changelogs), combine additions from both sides rather than picking one.
  - For generated or lock files (`package-lock.json`, `uv.lock`, etc.), prefer regeneration over manual merge.
  - If a conflict involves contradictory changes to the same lines, present the options and let the user decide.
  - After resolving, show the resolved diff and verify no conflict markers remain.

## Reporting

- Do not claim a command passed unless it was run.
- Do not invent tool output.
- Distinguish introduced failures from pre-existing ones.
