---
name: circuitpython-security-scan
description: Run a security audit on CircuitPython code using Ruff S rules and embedded-specific checks, fix findings iteratively, and re-validate until clean.
---

# CircuitPython Security Scan

Use this skill when the goal is to audit CircuitPython code for security issues.

Typical triggers:
- "scan for security issues"
- "audit this code for secrets or vulnerabilities"
- "check for hardcoded credentials"
- pre-release security review of embedded code

## Required outcomes

The task is not complete until:
- Ruff S (flake8-bandit) rules have been run on the scope
- embedded-specific security checks have been performed
- all findings are resolved or explicitly justified
- fixes do not introduce new Ruff or Pyright failures

## Embedded-specific checks

Beyond standard Ruff S rules, check for:
- Hardcoded WiFi passwords, SSIDs, or network credentials
- Hardcoded API keys, tokens, or secrets
- Unencrypted MQTT, HTTP, or socket connections (prefer TLS/SSL)
- Exposed debug or serial ports in production code
- Insecure OTA (over-the-air) update patterns
- Unprotected `settings.toml` secrets or `secrets.py` committed to version control

## Workflow

1. Identify the scope (file paths or "changed files"). Default to changed `.py` files.
2. Run `python -m ruff check <paths> --select S` to find security-related issues.
3. Manually review for embedded-specific issues listed above — these are not caught by Ruff.
4. Fix findings: replace hardcoded secrets with `settings.toml` loading, add TLS where possible, remove debug code from production paths.
5. Re-run Ruff S rules and Pyright to verify fixes: `python -m ruff check <paths> --select S && python -m pyright <paths>`.
6. Report: scope, findings count by category, fixes applied, remaining risks, regression check status.
