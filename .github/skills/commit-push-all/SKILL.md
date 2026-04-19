---
name: commit-push-all
description: "Stage all current changes, generate a commit message, commit, and push to the remote. Use when asked to commit and push everything."
---

# Commit and Push All

Use the **commit-push** skill in **all** mode to stage all changes, generate a commit message, commit, and push to the remote.

Run the full skill workflow (inspect → sync check → stage all → commit → push).

Stage and commit ALL changes in the working tree. Do not skip files based on their directory, origin, or apparent purpose (e.g. `.github/`, `.claude/` config files are valid changes).

If `git status` reports a completely clean working tree (no modified, staged, or untracked files), stop and say so.
If the local branch is behind or has diverged from the remote, stop and print the recovery command.

Return only: the commit message, commit result, push result, any blocker.
