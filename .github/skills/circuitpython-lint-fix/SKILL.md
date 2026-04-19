---
name: circuitpython-lint-fix
description: Run Ruff on a CircuitPython scope, auto-fix what it can, manually fix the rest, and re-validate until clean. Static analysis only — no pytest.
---

# CircuitPython Lint Fix

Use this skill when the goal is to find and fix all Ruff issues in a CircuitPython scope.

Typical triggers:
- "fix all Ruff issues in this module"
- "make this package Ruff-clean"
- "run Ruff and fix everything"
- pre-merge lint cleanup of touched files

The goal is a clean Ruff run on the requested scope with no regressions in Pyright.

## Required outcomes

The task is not complete until all of the following are true:
- Ruff has been run on the requested scope
- all fixable issues have been auto-fixed with `--fix`
- all remaining issues have been manually resolved
- fixes do not introduce new Pyright type-checking failures
- any `# noqa` added is justified with a specific rule code and a brief inline reason

Do not stop after one pass if issues remain.
Do not claim clean unless the final Ruff run actually shows zero issues in the scope.

## CircuitPython-specific considerations

- Some pyupgrade (UP) rules suggest syntax not supported by CircuitPython. CircuitPython tracks CPython more closely than MicroPython but still has gaps — type union syntax (`X | Y`) and some formatting upgrades may not be supported. Suppress with justification.
- Follow Adafruit coding conventions when fixing style issues.
- Validation is static analysis only — do not introduce pytest or other CPython test frameworks.

## Workflow

1. Identify the scope (file paths, "changed files" via `git diff --name-only`, or the current file). Default to changed `.py` files.
2. Run `python -m ruff check <paths> --fix` to apply safe auto-fixes.
3. Manually fix remaining issues. Prefer code fixes over suppressions.
4. Re-run `python -m ruff check <paths>` (without `--fix`) and iterate until zero issues.
5. Validate no regressions: `python -m pyright <paths>`. Fix any new issues.
6. Report: scope, issue count before/after, auto-fixed vs manual count, files changed, suppressions added, regression check status.
