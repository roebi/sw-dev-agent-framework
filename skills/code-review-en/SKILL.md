---
name: code-review-en
description: >
  Performs a structured code review against requirements and architecture docs.
  Checks correctness, test coverage, security, KISS/SOLID principles, and
  code style. Produces a review-checklist.md with pass/fail per criterion and
  a list of required fixes. Use after the implement phase and before release.
  Activate for trigger phrases like: "code review", "review this code",
  "review phase", "check the implementation", "audit the code",
  "does the code meet requirements", or "pre-release review".
license: CC BY-NC-SA 4.0
metadata:
  author: roebi
  spec: https://agentskills.io/specification
---

# Code Review

Reviews the implementation against requirements, architecture, and quality gates.
No-self-merge rule: every implementation must pass this review before release.
Output is written to `review-checklist.md`.

## Input

- `requirements.md` - the agreed requirements
- `architecture.md` - the agreed design
- Source files under `src/`
- Test files under `tests/`

## Output - review-checklist.md

```markdown
# Code Review Checklist

## Requirements Coverage

| FR | Covered by test | Test passes | Notes |
|---|---|---|---|
| FR-01 | yes/no | yes/no | |

## Architecture Compliance

- [ ] Module structure matches architecture.md
- [ ] No module has more than one responsibility
- [ ] Side effects are isolated per design

## Test Quality

- [ ] Every FR has at least one test
- [ ] Tests use descriptive names: test_<what>_<when>_<expected>
- [ ] No test depends on execution order
- [ ] Coverage >= 80%

## Security

- [ ] No secrets, passwords, or tokens in code or tests
- [ ] All external inputs are validated
- [ ] No arbitrary code execution from user input

## Code Quality

- [ ] No em-dashes or long-dashes in comments or strings (use hyphen-minus)
- [ ] No magic numbers - use named constants
- [ ] No dead code
- [ ] Functions are pure where possible

## Required Fixes

1. <issue> - <file:line> - <severity: critical | major | minor>
```

## Step-by-step Review Process

### Step 1 - Requirements traceability

For each FR in requirements.md:
- Find the test(s) that cover it
- Run the tests and confirm they pass
- If no test exists: add "missing test for FR-XX" as a CRITICAL fix

### Step 2 - Architecture compliance

Compare the actual file tree to architecture.md:
- Extra modules must be justified or removed
- Missing modules mean an FR is unimplemented
- Check that DI boundaries are respected

### Step 3 - Test quality review

For each test file:
- Is every test name descriptive?
- Does each test assert exactly one thing?
- Are fixtures used to avoid repetition?
- Run coverage: `uv run pytest --cov=src --cov-report=term-missing`
- If coverage < 80%: add "increase coverage" as a MAJOR fix

### Step 4 - Security scan

Check for:
- Hardcoded credentials (grep for "password", "secret", "token", "key =")
- Unvalidated file paths (path traversal risk)
- Shell injection (subprocess with shell=True + user input)

### Step 5 - Code quality

Run static analysis:
```bash
uv run ruff check src/ tests/
```
Any ruff error is a MAJOR fix.

Check ascii-safe-text rule: no em-dashes (U+2014) or en-dashes (U+2013).
```bash
grep -rn $'\u2014\|\u2013' src/ tests/ && echo "FAIL: dashes found" || echo "OK"
```

### Step 6 - Write review-checklist.md

Record all findings. Classify each issue:
- CRITICAL: blocks release (missing test, security flaw, FR not implemented)
- MAJOR: must fix before release (coverage, ruff error, arch violation)
- MINOR: fix in a follow-up (naming, style, minor refactor)

Announce to the orchestrator:

```yaml
phase: review
status: done | blocked
output: review-checklist.md - <N> critical, <M> major, <K> minor findings
```

If there are CRITICAL or MAJOR findings: set `status: blocked`.
The orchestrator must not advance to RELEASE until review is `status: done`
with zero CRITICAL and zero MAJOR findings.

## Fix and Re-review Loop

If blocked:
1. Fix each CRITICAL and MAJOR finding in the implementation
2. Re-run all tests (must stay green)
3. Re-run this review skill
4. Repeat until zero CRITICAL and zero MAJOR remain
