---
name: circuitpython-quality-gate
description: Run the standard CircuitPython quality gate (Ruff + Pyright static analysis only) for changed files or a specified scope. No pytest.
---

# CircuitPython Quality Gate

Use this skill when the goal is to validate CircuitPython code through static analysis.

CircuitPython repositories use static analysis only — no pytest.

## Verification discipline

Do not claim a check passed unless you ran the command and read the output in this session.
Do not use "should pass", "probably clean", or "looks correct" as substitutes for evidence.
Run Ruff and Pyright. Read each output. Then state the result.

If verification cannot be run, say so explicitly. Do not infer a result.

## Required outcomes

The task is not complete until all of the following are true:
- the validation scope has been identified
- Ruff has been run and all issues resolved
- Pyright has been run and all issues resolved
- the result has been reported plainly

## Workflow

1. Identify the scope.
   - Default to changed files (`git diff --name-only`) unless the user specifies paths.

2. Run Ruff.
   ```
   python -m ruff check <paths>
   ```
   Fix any issues found. Re-run until clean.

3. Run Pyright.
   ```
   python -m pyright <paths>
   ```
   Fix any type errors found. Re-run until clean.

4. Report the result.
   Include: scope used, commands run, pass/fail per tool, any remaining issues.

## Output format
Return:
- changed files
- commands run
- pass/fail by command with evidence (exit code, failure count, or key output line)
- failing excerpts
- smallest next action

## Decision rules

- Do NOT run pytest — CircuitPython projects do not use it.
- Fix issues in touched code only; do not wander into unrelated files.
- Prefer code fixes over suppression comments.
- If Pyright reports errors from missing CircuitPython or Adafruit stubs, note them as known limitations.
