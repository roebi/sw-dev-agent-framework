---
name: design-architecture-en
description: >
  Produces an architecture design for a software project from a structured
  requirements list. Outputs architecture.md covering module structure,
  data flow, technology choices, and testability constraints. Use when
  requirements are complete and the next step is planning the structure
  before writing any code. Activate for trigger phrases like: "design the
  architecture", "architecture phase", "plan the module structure",
  "create an architecture doc", "design this system", or "how should we
  structure this project".
license: CC BY-NC-SA 4.0
metadata:
  author: roebi
  spec: https://agentskills.io/specification
---

# Design Architecture

Translates requirements into a concrete, testable architecture.
Output is written to `architecture.md` in the project root.
No production code is written in this phase.

## Input

- `requirements.md` from the `gather-requirements-en` phase

## Output - architecture.md

```markdown
# Architecture

## Summary

One paragraph describing the overall design approach.

## Module Structure

<file tree>

## Components

### <ComponentName>
- Responsibility: <one sentence>
- Public interface: <key functions/classes>
- Dependencies: <other components>

## Data Flow

<sequence or diagram in prose>

## Technology Choices

| Decision | Choice | Rationale |
|---|---|---|

## Testability Constraints

- <DI boundary> - <why it enables testing>
- <pure functions> - <where side effects are isolated>

## Open Questions

- <unresolved decision>
```

## Step-by-step Instructions

### Step 1 - Read requirements

Load `requirements.md`. Identify:

- How many distinct responsibilities exist? (-> module count)
- What are the input/output boundaries? (-> CLI args, file I/O, API calls)
- What side effects exist? (-> I/O, network, filesystem, DB)

### Step 2 - Apply KISS

Start with the simplest structure that satisfies all requirements.
One module is better than three if the problem is small.
Add modules only when a single file would exceed one responsibility.

### Step 3 - Design for testability (mandatory)

Every design decision must answer: "How will we test this?"

Rules:
- Side effects (file I/O, network, DB) must be isolated behind interfaces or injected dependencies.
- Business logic must be in pure functions with no hidden dependencies.
- No global state. Pass state explicitly.
- CLI entry point is a thin wrapper over testable core logic.

### Step 4 - Choose technology stack

For Python projects follow these defaults unless requirements override:
- CLI: Typer (gives --install-completion free)
- Testing: pytest with pytest-cov
- Dependency management: uv
- Package structure: src layout
- Linting: ruff
- CI: GitHub Actions with Python 3.13 in matrix

### Step 5 - Define module structure

Draw the file tree. Every module listed must map to at least one FR.
Delete any module that cannot be traced to a requirement.

### Step 6 - Document testability constraints

For each side effect boundary, write the DI strategy:
- File I/O: pass Path objects, inject fs abstraction for testing
- Network: inject HTTP client, use responses library in tests
- Subprocess: inject runner callable, mock in tests

### Step 7 - Write architecture.md

Write the file to the project root. Announce to the orchestrator:

```yaml
phase: design
status: done
output: architecture.md written - <N> components, <M> open questions
```

## Handover to Implement Phase

Pass `requirements.md` and `architecture.md` as inputs to `apply-tdd-loop-en`.
Each FR becomes one or more TDD loop iterations.
The TDD loop must not deviate from the architecture without updating
`architecture.md` first.
