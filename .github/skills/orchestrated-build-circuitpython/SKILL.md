---
name: orchestrated-build-circuitpython
description: Run the standard multi-agent CircuitPython implementation workflow with multi-perspective codebase exploration, architecture design, and quality review
---

# Orchestrated Build — CircuitPython

Delegate to the **circuitpython-orchestrator** agent for the full multi-agent workflow.

For complex requests, run circuitpython-analyst with multiple exploration focuses:
- similar features and patterns
- architecture and abstractions
- integration points and dependencies

Synthesize findings, resolve all ambiguities with the user, and present architecture options before building.

Then delegate:
- implementation to circuitpython-builder
- validation to circuitpython-tester (Ruff + Pyright (static analysis only))
- diff review to circuitpython-reviewer (multi-perspective for large changes)

Keep a checklist.
End with a compact summary.