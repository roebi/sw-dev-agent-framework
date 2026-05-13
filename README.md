# SW Dev Agent Framework

An agentic framework that does exactly one thing: **software development**.

Built with TDD. Every line of production code was preceded by a failing test.

## What it is

A set of agent skills covering the full software development lifecycle,
plus a Python CLI orchestrator that coordinates them.

The framework is a living example of the pattern it encodes:
it was built using the same TDD process it teaches agents to follow.

## Skills

| Phase | Skill | Purpose |
|---|---|---|
| 1. Requirements | `gather-requirements-en` | Goal -> testable requirements |
| 2. Design | `design-architecture-en` | Requirements -> architecture |
| 3. Implement | `apply-tdd-loop-en` | Architecture -> tested code |
| 4. Review | `code-review-en` | Code -> reviewed + gated |
| 5. Release | `release-sw-project-en` | Reviewed code -> tagged release |
| Orchestrator | `orchestrate-sw-dev-en` | Coordinates all phases |

All skills follow the [agentskills.io specification](https://agentskills.io/specification).

## Install

```bash
uv pip install -e .
```

## Usage

```bash
sw-dev-agent start "Build a Python CLI tool that converts CSV to Markdown tables"
sw-dev-agent status
sw-dev-agent phases
sw-dev-agent --install-completion
```

## Architecture

```
sw-dev-agent-framework/
- skills/
  - orchestrate-sw-dev-en/
  - gather-requirements-en/
  - design-architecture-en/
  - code-review-en/
  - release-sw-project-en/
- src/sw_dev_agent/
  - phases.py
  - orchestrator.py
  - cli.py
- tests/
  - test_phases.py
  - test_orchestrator.py
  - test_skill_spec_compliance.py
```

## TDD Build History

RED -> GREEN -> REFACTOR - three iterations:

1. Phase model (phases.py) - 10 tests
2. Orchestrator + HandoverState (orchestrator.py) - 15 tests
3. Skill spec compliance (5 skills x 8 tests) - 70 tests

Total: 95 tests, 95 passing.

## License

Skills: CC BY-NC-SA 4.0 | Code: MIT
