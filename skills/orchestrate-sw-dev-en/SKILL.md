---
name: orchestrate-sw-dev-en
description: >
  Orchestrates the full software development lifecycle as an agentic pipeline.
  Delegates each phase to a focused sub-skill in order: gather requirements,
  design architecture, implement with TDD, review code, and release. Use when
  a user or agent wants to build a software project from a goal statement to
  a released artifact using a structured, test-driven process. Activate for
  trigger phrases like: "build a software project", "develop this from scratch",
  "orchestrate sw development", "run the full dev pipeline", or
  "implement this end to end".
license: CC BY-NC-SA 4.0
metadata:
  author: roebi
  spec: https://agentskills.io/specification
---

# Orchestrate SW Dev

Runs the full software development lifecycle as a sequential agentic loop.
Each phase delegates to a dedicated sub-skill. State is tracked in
`Handover-State.md` so the pipeline can be resumed across sessions.

## Lifecycle Phases

```
REQUIREMENTS -> DESIGN -> IMPLEMENT -> REVIEW -> RELEASE
```

| Phase | Skill | Output |
|---|---|---|
| 1. Requirements | `gather-requirements-en` | `requirements.md` |
| 2. Design | `design-architecture-en` | `architecture.md` |
| 3. Implement | `apply-tdd-loop-en` | passing tests + code |
| 4. Review | `code-review-en` | review checklist + fixes |
| 5. Release | `release-sw-project-en` | tagged release + changelog |

## Handover State

Track progress across sessions in `Handover-State.md`:

```yaml
# Handover-State.md
skill: orchestrate-sw-dev-en
goal: <one-sentence goal>
current_phase: requirements | design | implement | review | release
results:
  - phase: requirements
    status: done | pending | in_progress | blocked
    output: <brief summary or file reference>
```

## Orchestration Loop

```
LOOP:
  1. Read current_phase from Handover-State.md (or start at requirements)
  2. Load and run the sub-skill for that phase
  3. When the sub-skill completes, record its output in results[]
  4. Advance current_phase to the next phase
  5. Write updated Handover-State.md
  6. If current_phase has no next -> EXIT, project is released
```

## Entry Point

Input: a single goal statement, e.g.:

```
"Build a Python CLI tool that converts CSV files to Markdown tables."
```

Pass this goal to `gather-requirements-en` as the first phase input.

## Phase Gate Rules

- A phase must be `status: done` before the next phase starts.
- If a phase returns `status: blocked`, stop and report the blocker to the user.
- Never skip a phase. IMPLEMENT always uses TDD via `apply-tdd-loop-en`.
- REVIEW must run even if the developer wrote the code - no self-merge rule.

## Session Resume

If a session is interrupted, resume by:

```
1. Load Handover-State.md
2. Find the first phase where status != done
3. Re-run that phase's sub-skill with the existing context
```

## References

- `references/phase-contracts.md` - input/output contracts per phase
