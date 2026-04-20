---
name: security-threat-model
description: Build a STRIDE threat model from code-discovered architecture — identify trust boundaries, generate data flow diagrams, and map threats to mitigations. Complements code-level security-scan.
---

# Security Threat Model

## When to use

- "threat model this system"
- "what are the security risks in this architecture?"
- "STRIDE analysis"
- "identify trust boundaries"
- Pre-launch security architecture review

## Relationship to security-scan

- **security-scan** = code-level — Bandit/Ruff S rules, injection, secrets, unsafe patterns.
- **security-threat-model** = architecture-level — trust boundaries, data flows, attack surfaces.
- Use both together for comprehensive security coverage.

## Required outcomes

- System architecture discovered from actual code (not assumed).
- Data flow diagram in Mermaid format.
- Trust boundaries identified.
- STRIDE analysis per boundary-crossing flow.
- Mitigations mapped: what exists in code vs what is missing.
- Prioritized threat list.

## Workflow

### 1. Scope the system

Identify what to model — the full application, a single service, or a subsystem. If the system is too large, model the highest-risk subsystem first.

### 2. Discover architecture from code

Search the actual codebase for:

- **Entry points** — HTTP routes, CLI commands, message handlers, Tauri commands, gRPC services.
- **Data stores** — databases, files, caches, configuration, secrets storage.
- **External services** — third-party APIs, auth providers, message queues, CDNs.
- **Internal components** — modules, services, workers, and how they communicate.

### 3. Build data flow diagram

Generate a Mermaid DFD showing:

- Components, data stores, and external entities.
- Data flows between them, labeled with the data type (e.g., "auth token", "user PII", "config").
- Trust boundaries where privilege level changes.

### 4. Apply STRIDE per boundary-crossing flow

For each data flow that crosses a trust boundary, evaluate:

| Category | Question |
|----------|----------|
| **S**poofing | Can an attacker impersonate a legitimate entity? |
| **T**ampering | Can data be modified in transit or at rest? |
| **R**epudiation | Can actions be performed without an audit trail? |
| **I**nformation disclosure | Can sensitive data leak across the boundary? |
| **D**enial of service | Can the system be overwhelmed at this boundary? |
| **E**levation of privilege | Can an attacker gain higher access than intended? |

### 5. Map mitigations

For each identified threat, check whether the code already has a mitigation. Categorize as:

- **Mitigated** — control exists and is correctly implemented.
- **Partially mitigated** — control exists but has gaps.
- **Unmitigated** — no control found in code.

### 6. Generate prioritized report

Rank unmitigated threats by severity (likelihood × impact, using high/medium/low). Present the full report in the output format below.

## Decision rules

- Discover architecture from code, not from assumptions or documentation alone.
- Focus on boundary-crossing flows — internal flows within a single trust zone are lower priority.
- Severity = likelihood × impact (use high/medium/low, not numeric scores).
- Do NOT modify code — this skill is analysis-only.
- If the system is too large, model the highest-risk subsystem first and note what was excluded.

## Output format

````
### Threat Model: [System Name]

**Scope:** [what was modeled]

### Data Flow Diagram
```mermaid
[DFD here]
```

### Trust Boundaries
| Boundary | Between | Data Crossing |
|----------|---------|---------------|

### STRIDE Analysis
| # | Flow | Threat Type | Description | Severity | Mitigation Status |
|---|------|-------------|-------------|----------|-------------------|

### Unmitigated Threats (Priority Order)
1. [highest priority threat] — [recommended mitigation]
2. ...

### Summary
[1-3 sentences on overall security posture and top actions needed]
````
