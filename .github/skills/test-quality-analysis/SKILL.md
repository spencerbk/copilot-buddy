---
name: test-quality-analysis
description: Evaluate test effectiveness beyond coverage — detect weak assertions, over-mocking, and tests that would not catch real bugs. Score and triage tests for improvement.
---

# Test Quality Analysis

Use this skill when the goal is to evaluate whether tests actually catch bugs, not just inflate coverage numbers.

Typical triggers:
- "are these tests any good?"
- "evaluate test quality"
- "find weak or useless tests"
- "test audit"
- code review where test adequacy is questioned

This skill is different from `test-generation` and `pytest-coverage`:
- **test-generation** creates new tests from scratch for uncovered code.
- **pytest-coverage** raises coverage numbers by filling measured gaps.
- **test-quality-analysis** evaluates whether existing tests would actually catch real bugs. It is read-only — it does not modify tests.

## Required outcomes

The task is not complete until all of the following are true:
- each analyzed test is scored 1–5 on effectiveness
- tests are triaged as: delete (1), rewrite (2), improve (3–4), or keep (5)
- concrete recommendations are provided for every non-keep test
- a summary report covers overall test health and top-priority improvements

## Workflow

1. Identify the scope and framework.
   Accept whichever the user provides:
   - specific test files or directories
   - a module whose tests should be evaluated
   - "changed files" (use `git diff --name-only` to find test files)
   - "this file" (use the currently open file)
   - entire test suite

   Detect the test framework (pytest, unittest, etc.) and any relevant fixtures or conftest files.

2. Evaluate each test against quality heuristics.
   The core question for every test: **would this test fail if a real bug were introduced in the code it covers?**

   Heuristics to apply:

   - **Assertion strength.**
     Weak: `assert x`, `assert result`, `assert len(items)`.
     Medium: `assert len(items) > 0`, `assert result is not None`.
     Strong: `assert result == expected_value`, `assert error.message == "specific text"`.

   - **Over-mocking.**
     If >50% of a test is mock setup, it likely tests mock configuration rather than real behavior. Check whether the mocks replace internal collaborators that could run as real objects.

   - **Coverage-only tests.**
     Tests that call functions but assert nothing meaningful — they prove the function does not raise, but not that it produces correct results.

   - **Implementation coupling.**
     Tests that assert on internal method call order, private attribute values, or implementation details. These break on refactors but miss behavioral bugs.

   - **Missing edge cases.**
     Tests covering only the happy path. Check for absent boundary-value tests, empty-input tests, error-path tests, and None/null handling.

   - **Determinism risks.**
     Tests relying on wall-clock time, random values, filesystem ordering, network access, or shared mutable state without controlling those factors.

3. Score each test 1–5.
   - **1 — Actively harmful.** Provides false confidence or masks bugs (e.g., catches exceptions and asserts nothing, mocks the system under test). Recommend: delete and replace.
   - **2 — Very weak.** Would not catch any real bug in the covered code (e.g., `assert True`, asserts only that no exception was raised). Recommend: rewrite with meaningful assertions.
   - **3 — Adequate but gapped.** Catches some bugs but has clear weaknesses — missing edge cases, weak assertions on part of the result, or unnecessary implementation coupling. Recommend: improve with specific suggestions.
   - **4 — Good.** Solid behavioral test with minor improvement possible — e.g., could add one edge case or tighten an assertion. Recommend: improve or keep.
   - **5 — Strong.** Tests real behavior, covers edge cases, uses precise assertions, would catch realistic bugs. Recommend: keep.

4. Produce the triage report grouped by score.

5. For tests scored 1–3, provide specific improvement recommendations.
   Each recommendation must include:
   - what is wrong (concrete, not vague)
   - what bug class the test would miss because of it
   - what the test should do instead

## Decision rules

- Focus on behavior-testing effectiveness, not code style or naming conventions.
- A test achieving 100% branch coverage with `assert True` is worse than a test covering 50% with strong assertions.
- Prefer concrete examples: "this test would not catch a sign-flip in `calculate_total` because it only asserts `result > 0`" over vague "could be improved."
- Do not recommend deleting a test without explaining what coverage would be lost and how to replace it.
- Do not modify any test code — this skill is read-only analysis. Use `test-generation` or `pytest-coverage` to act on recommendations.
- When the scope is large, prioritize depth on critical code paths over shallow coverage of every test.

## Output format

```
### Test Quality Report

**Scope:** [files/modules analyzed]
**Tests analyzed:** N
**Health summary:** X strong, Y adequate, Z weak/harmful

### Triage

#### Delete (Score 1)
- `test_name` in `test_file.py` — [why it's harmful] — [what to replace it with]

#### Rewrite (Score 2)
- `test_name` — [why it's very weak] — [what it should test instead]

#### Improve (Score 3–4)
- `test_name` — [specific gap] — [concrete improvement]

#### Keep (Score 5)
- `test_name` — [why it's strong]

### Overall Assessment
[1–3 sentences on test suite health and top-priority improvements]
```
