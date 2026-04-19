---
name: commit-push
description: Generate a single-line commit message, commit changes, and push to the remote. Supports two modes — stage all changes or commit only staged files.
---

# Commit and Push

Use this skill when the goal is to commit changes with a generated message and push to the remote.

## Modes

This skill supports two modes, set by the calling prompt:

- **all** (default) — stage every change in the working tree (`git add -A`) before committing.
- **staged** — commit only files that are already staged. Do not run `git add`.

## Workflow

Complete this in exactly **3 terminal commands** (plus one optional user prompt) to minimize round-trips:

1. **Inspect** — run `git diff --stat ; git diff --cached --stat ; git status --short` as one chained command.
   - **all mode:** stop only if the output is completely empty — no diffs, no staged changes, **and** no untracked files. Untracked files (`??` in status) count as changes because `git add -A` will stage them.
   - **staged mode:** stop only if `git diff --cached --stat` is empty (nothing in the index). Untracked files do not matter — this mode does not run `git add`.
   - **Untracked file safety (all mode only):** If untracked files include likely non-source artifacts — binaries, images, compiled outputs, environment files (`.env`), database files, or OS metadata (`Thumbs.db`, `.DS_Store`) — **ask the user** before proceeding. They may belong in `.gitignore`. Everything else is intentional source content and must be staged without asking. Intentional source content includes but is not limited to: code, config, docs, markdown, `.github/` files (agents, prompts, skills, instructions, workflows), `.claude/` files (commands, agents, rules, hooks, settings), and any dotfile config directories. **Do not treat files managed by an external tool (e.g. copilot-config deploy) as artifacts — they are committed source content.**
2. **Sync check** — only if step 1 found changes that will be pushed. Run the following as one chained command:
   ```
   git fetch --quiet 2>&1 ; git rev-parse --abbrev-ref @{upstream} 2>&1 ; git rev-list --left-right --count HEAD...@{upstream} 2>&1
   ```
   Interpret the result:
   - **`git fetch` failed** (non-zero exit, network/auth error) — warn but **proceed**. The push itself will surface the real error if the remote is unreachable. Do not trust rev-list output against stale refs.
   - **No upstream tracking branch** (`@{upstream}` fails) — this is a first push. **Proceed** normally; there is nothing to be behind.
   - **Detached HEAD** — no meaningful upstream check. **Proceed** normally.
   - **`rev-list` output is `N 0`** (ahead only) — **proceed** normally.
   - **`rev-list` output is `0 0`** (even) — **proceed** normally.
   - **`rev-list` output is `0 M`** where M > 0 (behind) — **stop**. Print: "Local branch is behind the remote by M commit(s). Pull before pushing:" followed by `git pull --rebase origin <branch>`. Do not commit or push.
   - **`rev-list` output is `N M`** where both > 0 (diverged) — **stop**. Print: "Local branch has diverged from the remote (N ahead, M behind). Reconcile before pushing:" followed by `git pull --rebase origin <branch>` or `git merge origin/<branch>`. Do not commit or push.
   - **Force-push opt-out** — if the user explicitly requests a force push, skip the sync check entirely.
3. **Act** — run the appropriate command as one chained sequence:
   - **all mode:** `git add -A ; git commit -m "<message>" ; git push`
   - **staged mode:** `git commit -m "<message>" ; git push`

Do NOT run commands beyond these 3 steps (no `git remote -v`, no extra checks).

## Commit message rules

The message must be:
- a single line
- wrapped in double quotes
- concise and specific
- written in imperative mood when practical
- grounded in the actual changed files and behavior

Do not return:
- multiple options unless explicitly requested
- bullet lists
- explanatory text before or after the message
- a multi-line commit body

## Priorities

- Prefer concrete nouns and verbs over generic words like "update" or "fix stuff".
- Mention the main feature, workflow, or subsystem when that improves clarity.
- If the change set spans multiple related updates, summarize the common theme.

## Required output

Return only:
- the commit message used
- whether the commit succeeded
- whether the push succeeded
- any blocker, if the commit or push was not performed (including sync-check failures: local branch behind remote, or local branch diverged from remote)

## Final rule

Do not fabricate scope. Base the commit message on the actual current changes.

## Hard constraint — no editorial filtering

You are a mechanical executor. If `git status` reports changes, your job is to commit and push them — not to evaluate whether they are "meaningful," "worth committing," or "real source code." **Never skip, exclude, or refuse to commit files based on their directory, filename pattern, apparent origin, or perceived purpose.** The user decides what belongs in git; you execute.
