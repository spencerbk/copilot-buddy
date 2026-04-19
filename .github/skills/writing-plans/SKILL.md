---
name: writing-plans
description: "Use when you have an approved design or spec for a multi-step task, before touching code. Breaks work into bite-sized implementation tasks with exact file paths, complete code, and verification steps."
---

# Writing Implementation Plans

Write comprehensive implementation plans assuming the implementing agent has zero codebase context and needs explicit guidance. Document everything: which files to touch, code for each step, how to test it. DRY. YAGNI. TDD. Frequent commits.

## When to use

Use after a design has been approved (typically via the brainstorming skill) and before any code is written. Also use when an orchestrator or user provides a spec or requirements for a multi-step task.

## Scope check

If the spec covers multiple independent subsystems, suggest breaking it into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large ones that do too much.
- In existing codebases, follow established patterns. If a file you are modifying has grown unwieldy, including a split in the plan is reasonable.

## Task granularity

Each step is one action (2-5 minutes of work):
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

## Task structure

Each task must include:
- **Files:** exact paths to create, modify, or test
- **Steps:** numbered, each with complete code or exact commands
- **Verification:** exact command to run and expected output
- **Commit:** exact git commands with a descriptive message

## No placeholders

Every step must contain the actual content an engineer needs. These are plan failures — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the content — tasks may be read out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)

## Plan format

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**File map:** [Which files will be created or modified and what each one does]

---

### Task 1: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Test: `tests/exact/path/to/test_file.py`

**Steps:**
1. Write the failing test [complete test code]
2. Run test to verify it fails [exact command, expected failure]
3. Write minimal implementation [complete code]
4. Run test to verify it passes [exact command]
5. Commit [exact git commands]

### Task 2: ...
```

## Self-review

After writing the complete plan, check it against the spec:

- **Spec coverage:** Can you point to a task for each requirement? List any gaps.
- **Placeholder scan:** Search for any "TBD", "TODO", vague instructions, or missing code blocks. Fix them.
- **Type and name consistency:** Do types, method signatures, and names used in later tasks match what was defined in earlier tasks?

If you find issues, fix them inline.

## Transition

After the plan is complete:

- If an orchestrator is coordinating, hand the plan back for execution through the builder/tester loop.
- If standalone, proceed to implementation task by task, following TDD for each.
