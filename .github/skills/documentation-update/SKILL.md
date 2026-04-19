---
name: documentation-update
description: Update project-level documentation (README.md, /docs/) to reflect code changes — behavior changes, new features, API changes, renamed or removed functionality, and configuration changes.
---

# Documentation Update

Use this skill when code changes affect user-facing behavior and existing project documentation may need to reflect those changes.

Typical triggers:
- behavior change in a public API or CLI
- new feature, command, or configuration option
- renamed or removed functionality
- changed default values or environment variables
- new dependency or removed dependency that users interact with
- changed installation, setup, or usage steps

The goal is to keep existing documentation accurate and in sync with the code — not to write documentation from scratch or expand coverage beyond what already exists.

## Scope

- **In scope:** README.md, files under /docs/, and other project-level markdown documentation that already exists in the repository.
- **Out of scope:** inline docstrings, code comments, generated API docs, and changelog/release notes. Do not create new documentation files unless the change introduces an entirely new feature with no existing doc home.

## Required outcomes

The task is not complete until all of the following are true:
- every doc section that references changed behavior has been updated
- no stale references to renamed or removed functionality remain in touched docs
- code examples in touched docs are consistent with the current implementation
- relative links in touched docs still resolve correctly
- the update is minimal — do not rewrite sections that are unaffected by the code change

## Workflow

1. Identify changed behavior.
   - Review the code diff or analyst brief to understand what changed from the user's perspective.
   - Distinguish internal refactors (no doc impact) from behavior-visible changes (doc impact).
   - If the change is purely internal with no user-visible effect, report "no documentation impact" and stop.

2. Scan existing documentation.
   - Check README.md and /docs/ (if present) for sections that reference the changed behavior.
   - Search for mentions of renamed or removed symbols, commands, options, or paths.
   - Note any code examples or usage snippets that may be affected.

3. Update relevant sections.
   - Edit only the sections that reference changed behavior.
   - Keep the existing tone, structure, and level of detail — match the surrounding documentation style.
   - Update code examples to reflect the current API or usage.
   - Remove or replace references to renamed or removed functionality.
   - Add brief documentation for new user-visible features in the most natural existing location.

4. Validate the updates.
   - Confirm relative links in touched docs still resolve.
   - Confirm code examples are syntactically correct.
   - If the repository has a markdown linter configured, run it on touched files.

5. Report the result.
   Include:
   - which docs were updated and why
   - which docs were checked but needed no changes
   - any docs that could not be confidently updated (flag for human review)

## Decision rules

- If no existing documentation references the changed behavior, report "no documentation updates needed" — do not speculatively create new docs.
- Prefer minimal, targeted edits over rewriting entire sections.
- Do not embed volatile counts (test counts, file counts, target counts) in prose documentation — they silently go stale when the underlying codebase changes. Refer to the artifact by name (e.g., "`tests/test_foo.py`") without hardcoding a specific number.
- When in doubt about whether a change is user-visible, err on the side of checking the docs.
- Do not change documentation formatting, structure, or style beyond what is needed to reflect the code change.
