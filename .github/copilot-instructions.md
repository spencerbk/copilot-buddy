# Copilot Instructions — CircuitPython

## Validation commands

- Lint: `python -m ruff check <paths>`
- Type-check: `python -m pyright <paths>` (with CircuitPython stubs)

## Toolchain

- **Linting**: Ruff
- **Type checking**: Pyright (with circuitpython-stubs)
- **Testing**: Static analysis only — do not introduce pytest or unit test frameworks

## Key conventions

- Follow Adafruit coding conventions and library structure.
- Target memory-constrained environments; prefer minimal allocations.
- Use `adafruit_` prefixed libraries from the Adafruit CircuitPython Bundle.
- Keep modules small; large files consume more RAM at import time.
- Prefer `board` and `digitalio` / `analogio` over raw register access.
- Use type hints for public functions where Pyright can validate them, but do not add runtime typing imports.
- Prefer explicit names that match Adafruit community patterns.

## Hardware interaction

- Always document pin assignments and hardware assumptions in comments.
- Use `try/finally` to ensure hardware resources (I2C, SPI, UART, GPIO) are released on error.
- Follow the Adafruit driver pattern: `__init__` takes a bus object, properties expose sensor readings.
- Guard against repeated initialization of peripherals.

## Error handling

- Fail clearly; do not swallow exceptions.
- Provide concise error messages (long strings consume RAM).
- Validate external inputs (sensor data, serial input) at boundaries.

## Git operations

- Do not run `git commit` or `git push` unless the user explicitly asks you to commit and/or push.
- Making code changes does not imply permission to commit or push them.
- When the user wants to commit, they will invoke the commit-push skill or give an explicit instruction.
- Do not resolve merge conflicts by replacing the entire file with one side's version. This includes `git checkout --theirs`, `git checkout --ours`, and any whole-file side selection — these silently discard the other side's changes.
- When resolving merge conflicts:
  - Show the conflicting hunks from both branches so the user can see what would be kept and what would be lost.
  - For additive files (`.gitignore`, `requirements.txt`, config files, changelogs), combine additions from both sides rather than picking one.
  - For generated or lock files (`package-lock.json`, `uv.lock`, etc.), prefer regeneration over manual merge.
  - If a conflict involves contradictory changes to the same lines, present the options and let the user decide.
  - After resolving, show the resolved diff and verify no conflict markers remain.

## Reporting

- Do not claim a command passed unless it was run.
- Do not invent tool output.
- Distinguish introduced failures from pre-existing ones.

## Project-specific instructions

- Do not edit `copilot-instructions.md`, `CLAUDE.md`, or `CAPABILITIES.md` directly — they are managed by copilot-config and will be overwritten on the next deploy.
- Add project-specific instructions, conventions, and overrides to the **project-local instruction file** instead:
  - **Copilot:** `.github/instructions/project.instructions.md`
  - **Claude:** `.claude/rules/project.md`
- These files are never overwritten by deploy and are the correct place for repo-specific guidance.

## Warp tools

### Fast Apply (`edit_file`)

IMPORTANT: **Always prefer `edit_file` over `edit`, `str_replace`, or full file writes** for modifying existing files. It accepts partial code snippets — you do not need to read the full file just to perform the edit.

The edit is applied by a fast, speed-optimized merge model, so make each edit explicit and unambiguous while minimizing unchanged code.

**Key rules:**
- Use the literal marker `// ... existing code ...` for all unchanged sections, regardless of file language (Python, Rust, Swift, etc.). This is the token the merge engine matches.
- **Omitting the marker causes deletions** — always include it for unchanged sections above and below your edits.
- NEVER write out unchanged code — use the marker instead. Bias towards as few repeated lines as possible.
- Write a first-person `instructions` parameter (e.g., "I will add input validation") — this helps the merge engine achieve near-100% accuracy.
- Preserve exact indentation in the `code_edit` content.
- Batch multiple edits to the same file in one `edit_file` call.
- For deletions: show context before and after, omit the deleted lines.

When NOT to use `edit_file`:
- Creating brand-new files (use standard file creation tools)
- When `edit_file` fails on a retry (fall back to `edit`)

### Warp Grep (`codebase_search`)

`codebase_search` is a code search **subagent** — each call runs a separate LLM that performs multiple grep and file-read operations, reasons about relevance, and returns matching code. Searches take ~6 seconds and are billable. Use it judiciously.

**Use `codebase_search` when:**
- Exploring unfamiliar code ("how does billing work?", "where is auth handled?")
- Finding implementations scattered across multiple files
- Tracing a flow end-to-end across modules
- Locating code by behavior description, not by name

**Use `grep`/`glob` instead when:**
- You know the filename or pattern → `glob`
- You know the exact symbol, string, or error message → `grep`
- You need regex matching → `grep`
- A quick one-off lookup suffices (`grep` is <100ms vs ~6s)

**Never use `codebase_search` for:** filename lookups, exact function/class name searches, keyword dumps, or regex patterns.

### Agent integration

When `warp_grep` is enabled in deploy.json, MCP tools (`codebase_search` and `edit_file`) are automatically injected into agent workflows during deployment. Analysts and orchestrators get `codebase_search` for semantic exploration; builders and orchestrators get `edit_file` for efficient partial-snippet edits. No manual agent configuration is needed.

### Warp Grep setup (VS Code)

To enable warp-grep in VS Code, open the command palette and run **MCP: Open User Configuration**, then add:

```json
{
  "mcpServers": {
    "filesystem-with-morph": {
      "env": {
        "MORPH_API_KEY": "YOUR_API_KEY",
        "DISABLED_TOOLS": "none"
      },
      "command": "npx -y @morphllm/morphmcp",
      "args": []
    }
  }
}
```

### Warp Grep setup (Copilot CLI)

MCP servers for the Copilot CLI are configured in `~/.copilot/mcp-config.json` (note: **not** `mcp.json`):

```json
{
  "mcpServers": {
    "filesystem-with-morph": {
      "env": {
        "MORPH_API_KEY": "YOUR_API_KEY",
        "DISABLED_TOOLS": "none"
      },
      "command": "npx",
      "args": ["-y", "@morphllm/morphmcp"]
    }
  }
}
```

Run `/restart` then `/mcp` in the CLI to verify the server is connected.

### Troubleshooting

If MCP tools are not working, verify the Morph MCP server is running:
- **Copilot CLI:** Run `/mcp` to check server status. If disconnected, run `/restart`.
- **VS Code:** Check MCP server status in the Output panel (MCP channel).
- **Claude Code:** Check `.claude/.mcp.json` exists and the server is configured.

Agents will automatically fall back to standard tools (`grep`/`glob`/`view` and `edit`) when the MCP server is unavailable.

## Context7 documentation tools

Always use Context7 MCP when you need library or API documentation, code generation examples, setup or configuration steps — without the user having to explicitly ask. Context7 provides up-to-date, version-specific documentation and code snippets for programming libraries and frameworks.

### Workflow

1. **Resolve the library ID first:** Call `resolve-library-id` with the library name and a brief description of what you need. Select the best match based on name similarity, source reputation, and snippet coverage.
2. **Query documentation:** Call `query-docs` with the resolved library ID and a specific question. Be descriptive — "How to set up authentication with JWT in Express.js" is better than "auth".

### When to use Context7

- Looking up API signatures, function parameters, or return types for external libraries
- Finding code examples for library features (setup, configuration, common patterns)
- Verifying correct usage of a library API during code review or implementation
- Checking for version-specific behavior or breaking changes

### When NOT to use Context7

- For project-internal code (use `grep`, `glob` instead)
- For general programming concepts not tied to a specific library
- When the user has already provided the documentation or API details

### Graceful fallback

If Context7 is not connected or the MCP server is unavailable, fall back to web search (`WebSearch`/`WebFetch`) or built-in knowledge for library documentation. Do not error or stall — proceed with the best available information source.

### Context7 setup (VS Code)

Open the command palette and run **MCP: Open User Configuration**, then add:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

### Context7 setup (Copilot CLI)

MCP servers for the Copilot CLI are configured in `~/.copilot/mcp-config.json`:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

Run `/restart` then `/mcp` in the CLI to verify the server is connected.

### Troubleshooting

If Context7 tools are not working:
- **Copilot CLI:** Run `/mcp` to check server status. If disconnected, run `/restart`.
- **VS Code:** Check MCP server status in the Output panel (MCP channel).
- **Claude Code:** Check `.claude/.mcp.json` exists and the server is configured.

Agents will automatically fall back to web search and built-in knowledge when Context7 is unavailable.
