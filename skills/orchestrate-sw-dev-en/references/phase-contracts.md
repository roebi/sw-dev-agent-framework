# Phase Contracts

Input and output contract of every phase in the pipeline. A phase may
only start when all of its inputs exist, and is only `done` when all of
its outputs exist and its exit gate passes.

| Phase | Skill | Inputs | Outputs | Exit gate |
|---|---|---|---|---|
| 1. Requirements | `gather-requirements-en` | goal statement (Phase 0 intent) | `requirements.md` | Requirements Review checklist passed and approved |
| 2. Design | `design-architecture-en` | `requirements.md` | `architecture.md` | every module traces to a requirement; no new requirements added |
| 3. Implement | `apply-tdd-loop-en` | `requirements.md`, `architecture.md` | tests + code under `src/` and `tests/` | all requirements covered by passing tests (`exit_condition_met: true`) |
| 4. Review | `code-review-en` | `requirements.md`, `architecture.md`, `src/`, `tests/` | `review-checklist.md` | 0 CRITICAL and 0 MAJOR findings |
| 5. Release | `release-sw-project-en` | `review-checklist.md`, clean working tree | version bump, `CHANGELOG.md` entry, git tag, published artifact | tag pushed and artifact published |

## Status announcement

Every phase ends by announcing a status block to the orchestrator:

```yaml
phase: requirements | design | implement | review | release
status: done | blocked
output: <one-line summary or file reference>
```

## Send-back rules

- Design finds a missing requirement -> back to Requirements (Steps 2-7).
- Implement needs a structural change -> update `architecture.md` first.
- Review reports CRITICAL or MAJOR findings -> back to Implement, then Review again.
- Release gate fails -> `status: blocked`, report to the user.
