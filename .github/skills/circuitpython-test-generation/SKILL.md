---
name: circuitpython-test-generation
description: Generate validation scripts for CircuitPython modules that have zero or minimal tests. Analyze the public API, produce lightweight test scripts respecting CIRCUITPY filesystem constraints, and validate.
---

# CircuitPython Test Generation

Use this skill when the goal is to create validation scripts from scratch for CircuitPython code that has no or very few tests.

Typical triggers:
- "write tests for this module"
- "bootstrap validation scripts for this driver"
- "this file has no tests — add them"
- onboarding board support code that needs a safety net before modification

This skill is different from coverage skills:
- **Test generation** starts from zero and creates validation scripts based on the module's public API.
- Coverage skills start from existing tests and iterate on measured coverage gaps.

CircuitPython has no pytest or coverage tooling on-target. Tests are standalone scripts that import the module, exercise its API, and assert expected behavior. Be mindful of CIRCUITPY filesystem size limits — keep test files small.

## Required outcomes

The task is not complete until all of the following are true:
- a test script exists for the requested scope
- tests cover the public API: functions, classes, methods, and important module-level behavior
- tests cover normal paths, edge cases, and key error paths
- all generated tests pass when run with CPython (for host-testable logic) or on-device
- tests are deterministic, readable, and consistent with repository conventions
- no production code was changed unless a test revealed a genuine bug that was fixed

**Iron law — every test must assert something meaningful.** A test that only calls a function without checking its result is not a test.

## Workflow

1. Identify the scope.
   Accept whichever the user provides: a specific module, a driver, a library, or "this file."

2. Analyze the module's public API.
   - Identify all public functions, classes, methods, and constants.
   - Identify board/hardware dependencies that must be mocked (`board`, `digitalio`, `busio`, `analogio`).
   - Identify Adafruit library dependencies (`adafruit_bus_device`, `adafruit_register`, etc.).
   - Note which parts can run on a CPython host vs require a real board.

3. Generate tests.
   For each public symbol, generate tests covering:
   - **Happy path** — typical usage with expected output.
   - **Edge cases** — zero-length buffers, None handling, boundary values, memory pressure.
   - **Error paths** — expected exceptions, invalid pin assignments, missing libraries.

   Quality rules:
   - Use `assert` statements with descriptive messages: `assert result == 42, f"expected 42, got {result}"`.
   - Mock board peripherals at the boundary — create stub classes for `board.Pin`, `busio.I2C`, `busio.SPI`, `digitalio.DigitalInOut`.
   - Follow Adafruit library test patterns: stub the I2C/SPI device, then instantiate the driver with the stub.
   - Call `gc.collect()` in test setup to simulate constrained-memory conditions.
   - Keep test scripts small — CIRCUITPY filesystems are often 1–4 MB; one file per module, no heavy frameworks.
   - Guard host-only tests: `import sys; if sys.implementation.name != "circuitpython": ...`

4. Validate.
   - Run tests with `python3` for host-testable logic.
   - All tests must pass without error.
   - If any test reveals a genuine production bug, note it explicitly.

5. Report the result.
   Include:
   - module analyzed
   - test file created
   - number of assertions generated
   - public symbols covered vs total
   - pass/fail results
   - any symbols intentionally skipped (with reason)

## Decision rules

- Test behavior, not implementation details.
- Prefer real logic over mocks when the code is host-testable.
- Do not test private functions directly unless they represent critical internal logic.
- If board interaction cannot be mocked meaningfully, note it as a gap rather than forcing an artificial test.
- If the module has existing tests, extend them rather than creating a parallel file.
- Respect CIRCUITPY filesystem constraints — avoid generating large test files or many small ones.
