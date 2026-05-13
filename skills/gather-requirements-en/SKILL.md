---
name: gather-requirements-en
description: >
  Transforms a vague goal or feature request into a structured, testable
  requirements list. Produces a requirements.md with numbered functional
  and non-functional requirements. Use when a user or agent starts a new
  software project and needs to turn an idea into concrete, implementable
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

Converts a goal statement into a structured, numbered list of requirements
that are testable, unambiguous, and ready for architecture design and TDD.
Output is written to `requirements.md` in the project root.

## Input

A goal statement (one sentence to one paragraph), for example:

```
"Build a Python CLI tool that converts CSV files to Markdown tables."
```

## Output - requirements.md

```markdown
# Requirements

## Functional Requirements

FR-01: <verb> <what> <constraint>
FR-02: ...

## Non-Functional Requirements

NFR-01: <quality attribute> - <measurable target>
NFR-02: ...

## Out of Scope

- <explicitly excluded feature>
```

## Step-by-step Instructions

### Step 1 - Clarify the goal

Restate the goal in one sentence. Identify:

- The primary user or agent (who uses the output?)
- The core action (what must the software do?)
- The target platform (CLI, library, web service, container?)
- Key constraints (language, runtime, existing dependencies?)

### Step 2 - Derive functional requirements

Write one requirement per line. Each FR must be:

- **Testable** - you can write a test that passes or fails
- **Atomic** - one behaviour per requirement
- **Verb-first** - starts with an action: "Accept", "Return", "Validate", "Write"

Bad: "Handle files" -> too vague, not testable.
Good: "FR-01: Accept a CSV file path as a CLI argument and fail with exit code 1 if the file does not exist."

### Step 3 - Add non-functional requirements

Cover at least these where relevant:

- Performance (response time, throughput)
- Reliability (error handling, exit codes)
- Testability (test framework, coverage target)
- Portability (Python version, OS)
- Security (input validation, no secrets in output)

### Step 4 - Define out of scope

Explicitly list at least two things that are NOT in scope.
This prevents scope creep in later phases.

### Step 5 - Validate requirements

Before writing requirements.md, check each FR:

```
[ ] Can I write a test for this requirement? (testability gate)
[ ] Does it describe ONE behaviour? (atomicity gate)
[ ] Is it free of implementation detail? (requirements vs design)
[ ] Is it free of ambiguous words like "fast", "easy", "good"? (clarity gate)
```

Any FR that fails a gate must be rewritten or split.

### Step 6 - Write requirements.md

Write the file to the project root. Announce to the orchestrator:

```yaml
phase: requirements
status: done
output: requirements.md written with <N> functional and <M> non-functional requirements
```

## Handover to Design Phase

Pass `requirements.md` as the primary input to `design-architecture-en`.
The design phase must not add new requirements - only reference existing ones.
