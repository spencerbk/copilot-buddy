---
name: circuitpython-dependency-audit
description: Audit CircuitPython dependencies for unused imports, missing libraries, and Adafruit Bundle compatibility.
---

# CircuitPython Dependency Audit

Use this skill when the goal is to audit CircuitPython project dependencies.

Typical triggers:
- "check for unused imports"
- "audit my lib/ directory"
- "are all dependencies used?"
- pre-release dependency cleanup

## Required outcomes

The task is not complete until:
- all `.py` files have been scanned for import statements
- unused imports are identified
- missing libraries (imported but not in `lib/`) are identified
- findings are cross-referenced against CircuitPython built-in modules and the Adafruit Bundle
- findings are reported clearly

This is a diagnostic skill — report findings but do not auto-fix without user confirmation.

## What to check

1. **Unused imports** — modules imported but never referenced in the file or project.
2. **Missing libraries** — modules imported that are not built-in and not present in the `lib/` directory.
3. **Adafruit Bundle check** — verify that `adafruit_*` libraries in `lib/` are from the official Adafruit CircuitPython Bundle and note any outdated versions if detectable.

## Workflow

1. Identify the scope. Default to the project root.
2. Scan all `.py` files for import statements. Build an import graph.
3. Cross-reference imports against:
   - CircuitPython built-in modules (`board`, `digitalio`, `analogio`, `busio`, `time`, `json`, `os`, `struct`, `sys`, `gc`, `supervisor`)
   - files in `lib/` directory
   - local project modules
4. Run `python -m ruff check <paths> --select F401` to catch unused imports programmatically.
5. Report findings grouped by category: unused imports, missing libraries, Adafruit Bundle compatibility.
6. Suggest fixes but wait for user confirmation before applying changes.
