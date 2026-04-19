---
name: changelog-generation
description: Generate a changelog entry from commit diffs and PR descriptions. Supports tag-to-tag ranges, conventional commits, and Keep a Changelog format.
---

# Changelog Generation

Use this skill when the goal is to generate a structured changelog entry from recent commits.

## Workflow

### 1. Determine the range

Accept one of:
- **Tag-to-tag** — e.g., `v1.2.0..v1.3.0`
- **Commit range** — e.g., `abc123..def456`
- **Since last tag** (default) — `git log $(git describe --tags --abbrev=0)..HEAD`
- **All commits** — if no tags exist, use the full commit history

If the user specifies a range, use it. Otherwise default to "since last tag" and fall back to "all commits" if no tags are found.

### 2. Collect raw data

```
git log --oneline --no-merges <range>
git diff --stat <range>
```

If the repository uses squash-merge PRs, commit messages are likely already PR-title-style — use them directly without further summarization.

### 3. Detect commit convention

Check if ≥60% of commits in the range follow Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `style:`). If so, use prefix-based categorization. Otherwise, infer categories from the diff content and commit messages.

### 4. Categorize changes

Use [Keep a Changelog](https://keepachangelog.com/) categories:

| Category | What goes here |
|----------|----------------|
| **Added** | New features, new files, new capabilities |
| **Changed** | Behavior changes, API changes, updated dependencies |
| **Deprecated** | Soon-to-be-removed features |
| **Removed** | Removed features, deleted files |
| **Fixed** | Bug fixes |
| **Security** | Vulnerability fixes, security improvements |

Omit empty categories. Each entry should be a single concise line with a commit reference.

### 5. Determine the version string

Use, in priority order:
1. User-provided version string
2. Auto-detect from project files: `pyproject.toml` `[project.version]`, `Cargo.toml` `[package.version]`, `package.json` `version`, `Info.plist` `CFBundleShortVersionString`
3. If none found, ask the user

### 6. Generate the entry

Format:

```markdown
## [<version>] - <YYYY-MM-DD>

### Added
- Description of change (commit-ref)

### Fixed
- Description of fix (commit-ref)
```

Guidelines:
- Write entries from the user's perspective, not the developer's.
- Group related commits into a single entry when they represent one logical change.
- Include commit short-hashes as references (e.g., `abc1234`).
- Keep each entry to one line.

### 7. Write to CHANGELOG.md

- If `CHANGELOG.md` exists, prepend the new entry after the file header (title and description lines).
- If `CHANGELOG.md` does not exist, create it with a standard Keep a Changelog header:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).
```

- Validate: no duplicate version entries, no empty categories in the output.

## Edge cases

- **No tags exist** — use full commit history, ask user for the version string, note "Initial release" if appropriate.
- **Empty range** — no commits since last tag. Report "no changes to log" and stop.
- **Monorepo** — if the user specifies a directory scope, filter commits: `git log <range> -- <directory>`.
- **Squash-merge workflow** — commits are already PR-title-style. Use directly without further summarization.
- **Amend vs. new entry** — if the version already exists in CHANGELOG.md, ask the user whether to replace or append.

## Required outcomes

The task is not complete until:
- A well-formatted changelog entry exists in CHANGELOG.md
- The entry covers all commits in the specified range
- Categories are correct and non-empty
- The version string and date are present
- No duplicate version entries exist in the file
