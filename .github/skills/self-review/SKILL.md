---
name: self-review
description: "Iteratively review, fix, and re-verify your own work until it is complete and correct. Use when asked to review your work, verify changes, iterate until clean, or run a GO/NO-GO review loop."
---

# Self-Review — Iterative GO/NO-GO Loop

Review your own work in structured passes, fix issues as you find them, and repeat until everything is clean. This is not a code review for someone else's changes — it is a self-verification loop for work you just completed.

## When to use

- After completing an implementation task, before reporting done.
- When the user asks you to "review your work", "verify changes", "iterate until clean", or "make sure everything is correct".
- When the user asks for a GO/NO-GO review cycle.
- As a final quality pass after any multi-step change.

## Loop structure

Each iteration is one pass through the full review. The cycle is:

```
REVIEW → GO/NO-GO decision
  → If GO: confirm done, summarize
  → If NO-GO: fix issues, then re-enter REVIEW (counts as +1 loop)
```

**Loop limit:** Stop after 10 loops by default. If the user specifies a different limit, use that. If you hit the limit without reaching GO, report what remains unresolved.

## Review dimensions

Each REVIEW pass must check all of the following. Do not skip dimensions even if they seem unlikely to have issues.

1. **Completeness** — Does the work fully address the original request? Every requirement, every file, every edge mentioned. Look for partially implemented features, missing cases, or TODO/placeholder artifacts left behind.

2. **Correctness** — Are there stale references, broken cross-references, typos in identifiers, or logic errors? If the change renamed something, verify all references were updated. If it added something, verify nothing was left inconsistent.

3. **Consistency** — Do naming conventions, patterns, and style match the rest of the codebase? Are new additions consistent with each other and with existing code?

4. **Validation** — For any code change (non-.md files), running the project's test suite is always relevant and must not be skipped. Verify that test execution evidence exists from a prior step — the exact test command, exit code, and summary line from the runner. If evidence is missing or stale (predates your most recent code edit), re-run the test suite now. If the project has no tests, confirm this explicitly by searching for test files. Do not invent output. If a check fails, that is a NO-GO finding.

5. **Documentation** — If the change affects behavior, APIs, configuration, or user-facing functionality, do the docs (README, docstrings, comments, config examples) still reflect reality?

6. **Accessibility** — If the change has a user-facing surface (UI, CLI, visualization, generated output), verify: keyboard operability, screen-reader support (labels, ARIA, VoiceOver), adequate color contrast, text alternatives for visual elements, and motion sensitivity. Skip this dimension only when the change is purely internal with no user-facing surface.

7. **Scope discipline** — Did the changes stay within the requested scope? Flag any unintended side effects or scope creep that may have been introduced during implementation.

## GO criteria

A pass is **GO** only when:

- All seven review dimensions are clean — no issues found.
- All relevant validation commands pass.
- You can state concretely what was reviewed and why it is correct.

If you find even one issue, the pass is **NO-GO**.

## NO-GO response

When a pass is NO-GO:

1. List every issue found, grouped by dimension.
2. Fix each issue immediately — edit files, update references, adjust code.
3. After fixing, re-enter the REVIEW loop (this counts as the next iteration).

Do not batch issues across multiple loops. Fix everything you find in a single NO-GO pass before re-reviewing.

## Output format

**Per loop**, report a single status line:

```
Loop N: GO — all dimensions clean.
```
or
```
Loop N: NO-GO — [count] issues found: [brief list]. Fixing now.
```

**When GO is reached**, provide a final summary:

- Total loops completed.
- What was fixed across all NO-GO loops (if any). Be specific — file names, what changed, why.
- If no fixes were needed, say so plainly: "No issues found. Work is complete as implemented."

**If the loop limit is hit without GO**, report:

- Total loops completed.
- What was fixed.
- What remains unresolved and why.

## Discipline

- Do not rubber-stamp. Actually re-read the changed files. Actually re-run validation. A review that just says "looks good" without evidence is not a review.
- Do not fix things outside the original scope during self-review. If you notice unrelated issues, mention them but do not fix them — that is scope creep.
- Do not report a validation command as passing unless you ran it and saw the output.
- Track and report the loop count. Every re-entry after a NO-GO increments the count.
