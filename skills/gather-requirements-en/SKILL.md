---
name: gather-requirements-en
description: >
  Transforms a vague goal or feature request into a structured, testable,
  dependency-ordered requirements list, grouped by prefixed requirement-ID
  groups (e.g. R-CTRL-001) and tagged with a driver (compliance, parity,
  usability). Produces a requirements.md with a mandatory review step
  before approval. Use when a user or agent starts a new software project
  or feature and needs to turn an idea into concrete, implementable
  requirements before any code or design work begins. Activate for trigger
  phrases like: "gather requirements", "write requirements for", "what are
  the requirements", "define the requirements", "requirements phase", or
  "turn this goal into requirements".
license: CC BY-NC-SA 4.0
metadata:
  author: roebi
  spec: https://agentskills.io/specification
---

# Gather Requirements

Converts a goal statement into a structured, dependency-ordered set of
requirement groups that are testable, unambiguous, and ready for
architecture design and TDD. Output is written to `requirements.md` in
the project root.

## Prerequisite - Phase 0 (Intent Capture)

This skill does not invent the initial idea. It expects a rough,
solution-oriented input handed off from an earlier, informal phase where
the user states a goal following their own known working patterns
("I want to build X the way I usually do Y"). If no such input exists
yet, ask for it first in Step 1 - do not skip straight to formal
requirement groups from nothing. Phase 0 is considered complete once the
input contains enough to draft at least one requirement group in Step 2.

## Input

A goal statement (one sentence to one paragraph), for example:

```
"Build a Python CLI tool that converts CSV files to Markdown tables."
```

## Output - requirements.md

```markdown
# Requirements

## Requirement Groups

Groups are processed and approved in dependency order: groups with no
dependency on another group come first (convention over configuration).
List each group's dependencies explicitly, even if empty.

### R-<GROUP>-000 - <group name>
depends-on: none

R-<GROUP>-001: <verb> <what> <constraint>
  driver: compliance | parity | usability
R-<GROUP>-002: ...
  driver: ...

### R-<GROUP2>-000 - <group name>
depends-on: R-<GROUP>

R-<GROUP2>-001: ...
  driver: ...

## Non-Functional Requirements

NFR-01: <quality attribute> - <measurable target>
NFR-02: ...

## Out of Scope

- <explicitly excluded feature>

## Requirements Review

- [ ] Dependency order respected (no group approved before its dependencies)
- [ ] Every requirement has a driver
- [ ] No conflicting requirements across groups
- [ ] No gaps against the Phase 0 goal statement
- [ ] Parity-driven requirements have an explicit usage/adoption hypothesis
- [ ] Compliance-driven requirements reference the law/regulation and deadline
- [ ] Reviewed by: <name/agent> on <date>
```

## Step-by-step Instructions

### Step 0 - Confirm Phase 0 input exists

If the incoming goal statement is missing the "known working pattern"
context (see Prerequisite above), ask for it before proceeding. Do not
generate requirement groups from an empty or purely abstract goal.

### Step 1 - Clarify the goal

Restate the goal in one sentence. Identify:

- The primary user or agent (who uses the output?)
- The core action (what must the software do?)
- The target platform (CLI, library, web service, container?)
- Key constraints (language, runtime, existing dependencies?)

### Step 2 - Define requirement groups and their dependency order

Split the goal into requirement groups, each with a short prefix
(e.g. R-CTRL, R-AUTH, R-API). For each group, list which other groups
it depends on, if any.

Convention over configuration - default ordering rule:

1. Groups with `depends-on: none` are gathered and approved first.
2. A group may only move to "approved" once every group in its
   `depends-on` list is already approved.
3. If two groups have no dependency relation to each other, order
   between them does not matter - do not invent an artificial order.

#### Worked example - dependency order

A real project ended up with this correct order (each group depends only
on groups listed before it):

```
1.  R-STRUCT    - path builders                    depends-on: none
2.  R-CHAPTER   - read/write core entity            depends-on: none
3.  R-EXPORT    - external tool wrapper             depends-on: none
4.  R-VERSION   - changelog writer                  depends-on: none
5.  R-LANG      - shared validation constant        depends-on: R-STRUCT
    R-META      - metadata using that constant      depends-on: R-STRUCT
6.  R-CONTENT   - workflow over the core entity      depends-on: R-CHAPTER
7.  R-SKILLGEN  - workflow over the core entity      depends-on: R-CHAPTER
8.  R-TRANSLATE - workflow over the core entity      depends-on: R-CHAPTER
9.  R-INIT      - bootstrap combining several groups depends-on: R-STRUCT, R-LANG, R-META, R-CHAPTER
10. R-WEBGUI    - interface over nearly everything   depends-on: R-STRUCT, R-LANG, R-META, R-CHAPTER, R-CONTENT, R-SKILLGEN, R-TRANSLATE, R-EXPORT, R-VERSION
11. R-CLI       - interface combining two subsystems depends-on: R-INIT, R-WEBGUI
12. R-DEPLOY    - packages everything above          depends-on: all
```

Note the shape: groups 1-4 are independent leaves (data/IO primitives with
no cross-references). Group 5 introduces the first real dependency (a
shared constant reused elsewhere). Groups 6-8 are parallel workflows
built on the same core entity - they don't depend on each other, only on
it. Groups 9-12 are increasingly wide integration layers, ending in a
packaging group that depends on everything. This is the typical shape to
expect: primitives -> shared building blocks -> parallel workflows ->
integration layers -> packaging. Presentation order in requirements.md
does not have to match this build order - what matters is that the
`depends-on` field is accurate, so later phases (design, TDD) can derive
the real build order from it instead of assuming top-to-bottom.

### Step 3 - Derive requirements per group

Write one requirement per line, inside its group. Each requirement must
be:

- **Testable** - you can write a test that passes or fails
- **Atomic** - one behaviour per requirement
- **Verb-first** - starts with an action: "Accept", "Return", "Validate", "Write"
- **Driver-tagged** - tag with exactly one of:
  - `compliance` - required by a law or regulation; note the
    law/regulation and its effective deadline directly on the
    requirement
  - `parity` - matches a competitor or trend feature; must carry an
    explicit usage/adoption hypothesis (who will use it, why) or it is
    rejected in Step 5
  - `usability` - increases real usability; must carry a concrete pain
    point or user-observed friction it addresses

Bad: "Handle files" -> too vague, not testable, no driver.
Good: "R-CLI-001: Accept a CSV file path as a CLI argument and fail with
exit code 1 if the file does not exist. driver: usability (users
currently get a raw stack trace)."

### Step 4 - Add non-functional requirements

Cover at least these where relevant:

- Performance (response time, throughput)
- Reliability (error handling, exit codes)
- Testability (test framework, coverage target)
- Portability (Python version, OS)
- Security (input validation, no secrets in output)

### Step 5 - Define out of scope

Explicitly list at least two things that are NOT in scope.
This prevents scope creep in later phases.

### Step 6 - Validate requirements (per-requirement gate)

Before the group can enter review, check each requirement:

```
[ ] Can I write a test for this requirement? (testability gate)
[ ] Does it describe ONE behaviour? (atomicity gate)
[ ] Is it free of implementation detail? (requirements vs design)
[ ] Is it free of ambiguous words like "fast", "easy", "good"? (clarity gate)
[ ] Does it have exactly one driver tag? (driver gate)
[ ] If driver is "parity", is there a usage/adoption hypothesis? (parity gate)
[ ] If driver is "compliance", is the law/regulation and deadline named? (compliance gate)
```

Any requirement that fails a gate must be rewritten or split.

### Step 7 - Requirements Review (cross-group gate)

Once all groups have passed Step 6, run one review pass across the
whole requirements.md before it can become the approved plan:

```
[ ] Dependency order respected (no group approved before its dependencies)
[ ] No conflicting requirements across groups
[ ] No gaps against the Phase 0 goal statement
[ ] Parity-driven requirements re-checked - reject any without a real
    usage/adoption hypothesis (this is the gate against low-value
    "feature exists because it can now be built fast" additions)
[ ] Compliance-driven requirements re-checked against their deadline
```

Requirements that fail this review are sent back to Step 3, not
silently waved through. Only after this pass is requirements.md allowed
to freeze into the approved plan.

### Step 8 - Write requirements.md

Write the file to the project root, including the completed
Requirements Review checklist. Announce to the orchestrator:

```yaml
phase: requirements
status: done
output: requirements.md written with <N> requirement groups (<T> requirements total) and <M> non-functional requirements
review: passed
```

## Handover to Design Phase

Pass `requirements.md` as the primary input to `design-architecture-en`.
The design phase must not add new requirements - only reference existing
ones. If the design phase identifies a missing requirement, it must be
sent back through Step 2-7 of this skill, not added ad hoc.
