---
name: commit-push-staged
description: "Generate a commit message, commit only the already-staged files, and push to the remote. Does not stage additional changes."
---

# Commit and Push Staged

Use the **commit-push** skill in **staged** mode to commit only the already-staged files, generate a commit message, and push to the remote.

Do NOT run `git add`. Only commit what is already in the index.

If nothing is staged, stop and say so.
If the local branch is behind or has diverged from the remote, stop and print the recovery command.

Return only: the commit message, commit result, push result, any blocker.
