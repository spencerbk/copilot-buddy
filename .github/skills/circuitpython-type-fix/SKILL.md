---
name: circuitpython-type-fix
description: Run Pyright on a CircuitPython scope, fix all type errors iteratively, and re-validate until clean. Static analysis only — no pytest.
---

# CircuitPython Type Fix

Use this skill when the goal is to find and fix all type-checking errors in a CircuitPython scope.

Typical triggers:
- "fix all type errors in this module"
- "make this package pass Pyright"
- pre-merge type-error cleanup of touched files

The goal is a clean Pyright run on the requested scope with no regressions in Ruff.

## Required outcomes

The task is not complete until all of the following are true:
- Pyright has been run on the requested scope
- all type errors are resolved
- fixes do not introduce new Ruff failures
- any `# type: ignore` added is justified with an error code and a brief reason
- the final Pyright run shows zero errors in the scope

Do not stop after one pass if errors remain.

## CircuitPython-specific considerations

- CircuitPython type stubs (`circuitpython-stubs`) may not exist for all boards or libraries. If stubs are missing, note which types could not be checked and degrade gracefully.
- The `board`, `digitalio`, `analogio`, and device-specific modules may lack complete stubs.
- Follow Adafruit typing conventions when adding annotations.
- Validation is static analysis only — do not introduce pytest or other CPython test frameworks.

## Workflow

1. Identify the scope (file paths, "changed files", or the current file). Default to changed `.py` files.
2. Run `python -m pyright <paths>` and capture errors.
3. Fix errors in order of preference: add/correct annotations, narrow types, fix actual bugs, suppress (last resort).
4. Re-run Pyright after each batch. Iterate until zero errors.
5. Validate no regressions: `python -m ruff check <paths>`. Fix any new issues.
6. Report: scope, error count before/after, files changed, suppressions added, regression check status.
