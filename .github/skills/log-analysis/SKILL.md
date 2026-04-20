---
name: log-analysis
description: Analyze source code logging patterns for silent catches, missing correlation IDs, secrets in log output, inconsistent levels, and structural gaps. Reviews code, not runtime logs.
---

# Log Analysis

Analyze source code logging patterns for gaps, inconsistencies, sensitive data leaks, and missing correlation. This skill reviews code — not runtime log files.

## When to use

- "audit logging in this module"
- "check for logging gaps"
- "find silent catches"
- "are we logging secrets?"
- Pre-production logging review

## Required outcomes

- Logging framework and configuration identified
- Findings categorized by severity with specific file/line references
- Recommendations with concrete fix examples

## Workflow

### 1. Discover logging framework and configuration

Identify the framework in use and how it is configured:

- **Python:** `logging`, `structlog`, `loguru` — check for handlers, formatters, log level settings
- **TypeScript:** `winston`, `pino`, `console.*` — check for transports, level config
- **Rust:** `tracing`, `log`, `env_logger` — check for subscribers, filters, `RUST_LOG`

Search for log level configuration, formatter setup, and handler/transport registration.

### 2. Analyze logging patterns

Scan the requested scope for these categories, in priority order:

1. **Silent catches** — `except`/`catch`/`Err` blocks with no logging or re-raise. Highest priority — these hide failures silently.
2. **Sensitive data in logs** — passwords, tokens, API keys, PII, credentials, or secrets passed to any log statement, including debug level.
3. **Log level misuse** — errors logged as info/debug, routine operations logged as warning/error.
4. **Missing context** — log messages like `"operation failed"` without identifying which operation, what input, or why.
5. **Missing correlation** — request/operation IDs not propagated through call chains; no way to trace a request across functions.
6. **Inconsistent structure** — mix of structured (key-value) and unstructured (format-string) logging in the same module.

### 3. Categorize findings by severity

| Severity | Examples |
|----------|----------|
| **CRITICAL** | Secrets/PII in log output; silent catches hiding errors |
| **MAJOR** | Missing error logging on failure paths; wrong log levels on errors |
| **MINOR** | Inconsistent structure; missing correlation IDs; verbose debug logging |
| **NIT** | Style inconsistencies; minor formatting differences |

## Decision rules

- Silent catches that swallow exceptions are always high severity.
- Secrets in logs are always critical — even in debug-level statements.
- Focus on error and failure paths first — missing happy-path logging is lower priority.
- Distinguish intentionally silent operations (documented with a comment) from accidentally silent ones.
- Do **NOT** modify code — this skill is analysis-only.

## Output format

Present results in this structure:

```
### Log Analysis Report

**Scope:** [files/modules analyzed]
**Framework:** [detected logging framework and configuration summary]
**Findings:** N critical, N major, N minor

### Findings

#### Critical
- **[Title]** — `file.py:42` — [description] — [recommended fix]

#### Major
- **[Title]** — `file.py:88` — [description] — [recommended fix]

#### Minor
- **[Title]** — `file.py:120` — [description] — [recommended fix]

### Logging Health Summary
[2-3 sentences on overall logging quality and top priorities]
```

If no findings exist for a severity level, omit that section. Always include the health summary.
