# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-30

### Added

- `gather-requirements-en`: requirement groups now carry an explicit
  `depends-on` field; groups with no dependency are gathered and
  approved first (convention over configuration).
- `gather-requirements-en`: mandatory `driver` tag per requirement
  (`compliance` | `parity` | `usability`), with compliance requirements
  required to name the law/regulation and deadline, and parity
  requirements required to carry a usage/adoption hypothesis.
- `gather-requirements-en`: new cross-group Requirements Review step
  (Step 7) that must pass before requirements.md can freeze into the
  approved plan; checks dependency order, conflicts, gaps, and re-checks
  parity/compliance requirements.
- `gather-requirements-en`: new Phase 0 (Intent Capture) prerequisite -
  the skill now expects, and asks for if missing, an informal
  solution-oriented goal statement before deriving requirement groups.
- `gather-requirements-en`: worked example of a correct dependency order
  across primitives, shared building blocks, parallel workflows,
  integration layers, and a packaging group.

## [0.1.1] - 2026-05-13

### Added

- Initial release of the 5-phase pipeline: REQUIREMENTS -> DESIGN ->
  IMPLEMENT -> REVIEW -> RELEASE.
- `gather-requirements-en`: goal statement to numbered FR/NFR
  requirements.md, with testability/atomicity/clarity validation gates
  and an out-of-scope section.
