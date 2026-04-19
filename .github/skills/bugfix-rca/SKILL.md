---
name: bugfix-rca
description: "After a bugfix, run a brief root cause analysis: categorize the bug, identify how it could have been caught earlier, implement prevention measures, and store the lesson learned."
---

# Bugfix RCA — Root Cause Analysis and Prevention

Run a brief post-fix analysis to understand why a bug wasn't caught earlier, implement prevention measures, and store the lesson for future sessions.

This is not a heavyweight postmortem. Keep it concise and actionable.

## When to use

- After a bugfix is complete and validated (chained from a `*-bugfix` skill)
- When an orchestrator completes a bugfix request and enters the RCA phase
- When explicitly asked to analyze a past fix for prevention opportunities

## Inputs

This skill expects the bugfix to already be done. You should have (from the preceding bugfix work):
- The failure signal (what went wrong)
- The root cause (what caused it)
- The fix applied (what changed)
- The regression test added (if any)

If these are not available from context, briefly reconstruct them from the current diff and recent work before proceeding.

## Workflow

### 1. Check for known patterns

Before analyzing, check if this bug matches a previously learned pattern. Use this priority order:

1. **Current session context** — The most common path is a self-review or bugfix loop immediately preceding this RCA. Check your current conversation history for the bug details, fix applied, and any regression test. This is usually sufficient to identify the bug pattern without any external queries.

2. **Repository memories** — Check `repository_memories` (if present in your system prompt) for stored lessons from past bugfix RCA runs. These are stored via `store_memory` and contain searchable bug-pattern summaries.

3. **Session store** — If the `sql` tool is available with `database: "session_store"`, search past sessions for related RCA entries. The `search_index` table is an FTS5 virtual table with these columns: `content`, `session_id` (UNINDEXED), `source_type` (UNINDEXED), `source_id` (UNINDEXED). Example query:
   ```sql
   SELECT content, session_id, source_type
   FROM search_index
   WHERE search_index MATCH 'bug OR lesson OR regression OR root cause'
   ORDER BY rank LIMIT 10
   ```
   Do not reference columns that are not listed above — the table has no other columns.

If a known pattern matches, note it and check whether the previous prevention was insufficient or whether this is a new instance of the same class.

### 2. Categorize the root cause

Classify using one of these standard categories:

| Category | Examples |
|----------|----------|
| **Logic error** | Off-by-one, wrong comparison, incorrect algorithm |
| **Missing validation** | No input checking, missing bounds check, unchecked return value |
| **Edge case not covered** | Empty input, null/nil, boundary values, Unicode, timezone |
| **Data shape / type mismatch** | Wrong type assumption, schema drift, serialization error |
| **Concurrency / timing** | Race condition, deadlock, stale closure, missing await |
| **Configuration / environment** | Wrong path, missing env var, platform-specific behavior |
| **Dependency issue** | Breaking update, API change, version mismatch |
| **Missing test coverage** | Behavior existed but was never tested |
| **Error handling gap** | Swallowed exception, missing fallback, incomplete recovery |
| **API contract violation** | Caller/callee disagreement on inputs, outputs, or side effects |
| **Unbounded external consumption** | No pagination cap, missing limit parameter, missing timeout, infinite retry, rate-limit exceeded, cost overrun from external API or feed |

State the category and a one-sentence explanation.

### 3. Analyze the detection gap

Determine where in the development pipeline this bug could have been caught earliest:

| Detection point | What would catch it |
|----------------|-------------------|
| **Static analysis** | Lint rule, type annotation, compiler warning |
| **Unit test** | Focused test on the specific behavior |
| **Integration test** | Test covering the interaction between components |
| **Code review** | Reviewer spotting the pattern or missing check |
| **CI/CD pipeline** | Automated check, build flag, or quality gate |
| **Runtime monitoring** | Log alert, error rate spike, health check |

State:
- The earliest detection point that could have caught this
- What specific check was missing or inadequate
- Whether the gap was a missing check entirely or an existing check that was too weak

### 4. Implement prevention measures

Based on the detection gap, implement concrete prevention. Choose from:

- **New test case** — Write a test that specifically targets the bug pattern, not just the specific instance. The test should catch the *class* of bug, not just this one occurrence.
- **Stronger type annotations** — Add types that make the bug impossible at compile/check time.
- **Lint rule or configuration** — Enable or configure a lint rule that flags this pattern.
- **Validation logic** — Add input validation, bounds checking, or contract enforcement in the code.
- **Documentation** — Update docs if the fix changes behavior or reveals a non-obvious pattern.

Keep prevention proportional to the bug. A typo doesn't need a new lint rule. A systemic validation gap does.

For MicroPython and CircuitPython: prevention is limited to static analysis (Ruff + Pyright), code-level guards, and documentation. Do not add pytest-based tests.

### 5. Validate prevention

Run the ecosystem-appropriate validation to confirm prevention measures work:
- The new test (if added) passes
- Lint and type checks pass on changed files
- Existing tests still pass

### 6. Store the lesson learned

Create a structured lesson in this format:

```
**Lesson Learned**
- Bug pattern: [category from step 2]
- What happened: [one sentence — the symptom]
- Root cause: [one sentence — the defect]
- Detection gap: [what check was missing]
- Prevention added: [what was implemented in step 4]
- Key insight: [one-sentence takeaway for future work]
```

**Memory storage:**
- If `store_memory` is available: store the lesson as a repository-scoped memory. Use a clear, searchable summary (e.g., "Bug lesson: missing validation on API input caused crash — added bounds-check test").
- If memory tools are not available: output the lesson block clearly in your response. It will be captured in session history for future `session_store` queries.
- In either case, always output the lesson block visibly in your response.

### 7. Brief report

Summarize in 5-8 lines:
- Root cause category
- Detection gap
- Prevention measures implemented
- Lesson stored (where — `store_memory` or session output)
- Any follow-up recommendations (e.g., "check other endpoints for the same missing validation")

## Decision rules

- Keep it brief. This is a 2-5 minute analysis, not a full incident review.
- Prevention should be concrete and implemented, not just recommended.
- If no meaningful prevention measure exists beyond the regression test already added, say so — do not invent busywork.
- Do not broaden scope to fix unrelated issues discovered during analysis.
- If the bug reveals a systemic pattern (e.g., missing validation across many similar code paths), note this as a follow-up recommendation but do not fix all instances now.
- When sweeping the codebase for instances of a bug pattern, search for the *class* of problem (e.g., all hardcoded counts, all unchecked returns), not just the specific regex that triggered the original find. Narrow sweeps miss sibling instances of the same defect.
