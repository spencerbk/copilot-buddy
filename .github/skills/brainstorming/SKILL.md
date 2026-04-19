---
name: brainstorming
description: "Use before any creative work -- creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements, and design before implementation."
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you are building, present the design and get user approval.

## Hard gate

Do NOT write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to every project regardless of perceived simplicity.

## Anti-pattern: "This is too simple to need a design"

Every project goes through this process. A utility function, a config change, a single-endpoint API -- all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you must present it and get approval.

## Workflow

1. Explore project context.
   - Check files, docs, recent commits.
   - Understand the current state before proposing anything.

2. Assess scope.
   - If the request describes multiple independent subsystems, flag this immediately.
   - If too large for a single spec, help decompose into sub-projects. Each gets its own design cycle.

3. Ask clarifying questions.
   - One question at a time. Do not overwhelm with multiple questions in a single message.
   - Prefer multiple-choice questions when possible.
   - Focus on understanding: purpose, constraints, success criteria.

4. Propose 2-3 approaches.
   - Present options conversationally with trade-offs.
   - Lead with your recommendation and explain why.
   - Present the minimum viable set of approaches -- do not enumerate every possibility.

5. Present the design.
   - Scale each section to its complexity: a few sentences if straightforward, more detail if nuanced.
   - Ask after each section whether it looks right so far.
   - Cover: architecture, components, data flow, error handling, accessibility (when the feature has a user-facing surface), testing strategy.
   - Be ready to go back and revise if something does not make sense.

6. Get explicit user approval.
   - Do not proceed to implementation until the user confirms the design.
   - If changes are requested, revise and re-present.

## Design principles

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently.
- YAGNI ruthlessly. Remove unnecessary features from all designs.
- Design for accessibility from the start. When the feature has a user-facing surface (UI, CLI, visualization, generated output), include accessibility requirements in the design: keyboard navigation, screen-reader support, color contrast, text alternatives, and motion sensitivity. These are not afterthoughts — they are design constraints.
- In existing codebases, explore the current structure first and follow existing patterns. Where existing code has problems that affect the work, include targeted improvements as part of the design. Do not propose unrelated refactoring.

## Working in existing codebases

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work (a file that has grown too large, unclear boundaries, tangled responsibilities), include targeted improvements as part of the design.
- Do not propose unrelated refactoring. Stay focused on what serves the current goal.

## Key principles

- One question at a time -- do not overwhelm with multiple questions.
- Multiple choice preferred -- easier to answer than open-ended when possible.
- YAGNI ruthlessly -- remove unnecessary features from all designs.
- Explore alternatives -- always propose 2-3 approaches before settling.
- Incremental validation -- present design, get approval before moving on.
- Be flexible -- go back and clarify when something does not make sense.

## Transition to implementation

After the user approves the design:
- If an orchestrator is coordinating, hand the approved design back with a clear summary suitable for creating an implementation plan.
- If standalone, transition to the writing-plans skill if available, or proceed to implementation with the approved design as the guide.

Do NOT skip straight to code after design approval. A plan should exist between design and code for any non-trivial work.
