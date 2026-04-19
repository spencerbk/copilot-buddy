---
name: circuitpython-refactor
description: Safely refactor CircuitPython code within a bounded scope while preserving behavior and following Adafruit conventions. Uses static analysis only — no pytest.
---

# CircuitPython Refactor

Use this skill when the goal is to restructure CircuitPython code without changing behavior.

Typical triggers:
- safe refactor
- cleanup without behavior change
- extract helper
- simplify control flow
- reduce duplication
- reorganize a bounded module or function
- improve Adafruit library or driver structure

The goal is to improve code structure while keeping behavior stable unless the user explicitly asks for a behavior change.

## Required outcomes

The task is not complete until all of the following are true:
- the refactor scope is bounded and stated clearly
- behavior is preserved (unless a change was explicitly requested)
- Adafruit conventions and driver patterns are followed
- memory efficiency is maintained or improved
- the fix does not introduce new Ruff or Pyright errors
- no unrelated code was changed

## Workflow

1. Identify the exact refactor scope and any hardware or CIRCUITPY storage constraints.
2. Analyze current structure.
   - Before refactoring, understand what exists: read the affected modules, trace dependencies, identify the specific code smell or structural problem.
   - Identify duplication, excessive nesting, hidden coupling, or naming problems.
   - Prefer the smallest structural change that materially improves the code.
3. State the behavior that must remain stable.
4. Implement the smallest structural improvement.
   - Follow Adafruit library conventions and driver patterns.
   - Prefer `board` pin names and `adafruit_bus_device` abstractions.
   - Keep import graphs small and memory-efficient.
   - Prefer extracting helpers over deep nesting.
5. Validate with static analysis.
   - Run Ruff on changed files.
   - Run Pyright on changed files.
   - Do NOT use pytest — CircuitPython projects use static analysis only.
6. Report the result.
   Include: refactor scope, behavior-preservation summary, files changed, validation results.

## Decision rules

- Preserve behavior unless explicitly asked to change it.
- Follow Adafruit conventions when restructuring driver or library code.
- Do not increase memory footprint without justification.
- Do not add imports or dependencies unless the refactor requires them.
- Keep diffs focused and minimal.
- If the refactor reveals a bug, note it explicitly and fix it only if tightly coupled.

## Output format

Return:
1. Files changed
2. What was refactored and why
3. Validation results (Ruff + Pyright on changed files — board compatibility checks where applicable)
4. Any remaining issues or trade-offs
