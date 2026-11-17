---
name: release-sw-project-en
description: >
  Performs the release phase of a software project: bumps version, generates
  changelog, creates a git tag, and publishes the artifact (PyPI, npm, or
  GitHub Release). Uses semver, conventional commits, and PyPI Trusted
  Publishing (OIDC) for Python packages. Use after code review passes with
  zero critical or major findings. Activate for trigger phrases like:
  "release the project", "release phase", "publish to PyPI", "create a
  release", "bump version and tag", "cut a release", or "ship it".
license: CC BY-NC-SA 4.0
metadata:
  author: roebi
  spec: https://agentskills.io/specification
---

# Release SW Project

Executes the final phase of the SW dev lifecycle: version bump, changelog,
git tag, and artifact publish. Only runs after `code-review-en` reports
zero CRITICAL and zero MAJOR findings.

## Pre-conditions (gate check)

Before starting, verify:

```
[ ] review-checklist.md exists and shows 0 CRITICAL, 0 MAJOR findings
[ ] All tests pass: uv run pytest
[ ] No uncommitted changes: git status --short (must be empty)
[ ] Git remote is reachable
```

If any gate fails: stop and report to orchestrator as `status: blocked`.

## Step 1 - Determine version bump

Read commit messages since the last tag using conventional commits:

```bash
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

Apply semver bump rules:
- Any `feat:` commit -> MINOR bump (0.x.0)
- Any `fix:` commit only -> PATCH bump (0.0.x)
- Any `BREAKING CHANGE:` in commit body -> MAJOR bump (x.0.0)
- First release with no prior tag -> 0.1.0

## Step 2 - Update version in pyproject.toml

```bash
# Read current version
current=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

# Compute new version (semver bump)
new_version=<computed>

# Update pyproject.toml
sed -i "s/version = \"$current\"/version = \"$new_version\"/" pyproject.toml
```

## Step 3 - Generate CHANGELOG entry

Append to `CHANGELOG.md`:

```markdown
## [<new_version>] - <YYYY-MM-DD>

### Added
- <feat commit summaries>

### Fixed
- <fix commit summaries>

### Changed
- <refactor commit summaries>
```

## Step 4 - Commit version bump

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v<new_version>"
```

## Step 5 - Tag the release

```bash
git tag -a "v<new_version>" -m "Release v<new_version>"
git push origin main --tags
```

## Step 6 - Publish artifact

### Python package (PyPI)

Use PyPI Trusted Publishing (OIDC) - no API token needed:

Trigger the GitHub Actions release workflow (must already be configured):
```bash
# The tag push triggers the workflow automatically
# Workflow must use pypa/gh-action-pypi-publish with:
#   environment: name: pypi
#   permissions: id-token: write
#   attestations: true
```

### npm package

```bash
npm publish --access public
```

### GitHub Release only

```bash
gh release create "v<new_version>" --title "v<new_version>" --notes-file <(git log ...)
```

## Step 7 - Announce completion

```yaml
phase: release
status: done
output: v<new_version> tagged and published - <artifact location>
```

Write final `Handover-State.md` update:

```yaml
current_phase: release
results:
  - phase: release
    status: done
    output: v<new_version> released
exit_condition_met: true
```

## Post-release

- Close or archive the working branch
- Update project README badge if applicable
- Announce on relevant channels

## Semver Rules and Examples

Version format: `MAJOR.MINOR.PATCH` (see https://semver.org/spec/v2.0.0.html).

| Change | Bump | Example |
|---|---|---|
| Incompatible API or behaviour change (`BREAKING CHANGE:` in commit body, or `!` after the type, e.g. `feat!:`) | MAJOR | 1.4.2 -> 2.0.0 |
| New backwards-compatible feature (`feat:`) | MINOR | 1.4.2 -> 1.5.0 |
| Backwards-compatible bug fix only (`fix:`) | PATCH | 1.4.2 -> 1.4.3 |
| `docs:`, `test:`, `chore:`, `ci:`, `refactor:` only | no release needed | - |

### Rules

- The highest-ranked change since the last tag decides the bump.
- A bump resets the lower parts: MINOR bump sets PATCH to 0; MAJOR bump sets MINOR and PATCH to 0.
- While MAJOR is 0 (`0.y.z`), the API is unstable; breaking changes bump MINOR.
- Never re-use or move a published version tag. A broken release is fixed by a new PATCH release.
- Software version tags use the form `vX.Y.Z`.

### Examples

```
v1.2.0..HEAD: fix: handle empty file          -> v1.2.1
v1.2.0..HEAD: feat: add --output flag         -> v1.3.0
v1.2.0..HEAD: feat!: drop Python 3.11 support -> v2.0.0
```

## PyPI Trusted Publishing (OIDC) Setup

Trusted Publishing lets a GitHub Actions workflow publish to PyPI without
an API token. PyPI trusts a short-lived OIDC token issued by GitHub for a
specific repository, workflow file and environment.

### One-time setup on PyPI

1. Open https://pypi.org/manage/account/publishing/ (new project) or the
   project's "Publishing" settings (existing project).
2. Add a GitHub publisher with:
   - Owner: `<github-owner>`
   - Repository: `<repo-name>`
   - Workflow name: `release.yml`
   - Environment: `pypi`

### One-time setup on GitHub

Create the environment `pypi` under Settings -> Environments. Optionally
add required reviewers so every publish needs a manual approval.

### Workflow

```yaml
on:
  push:
    tags: ["v*.*.*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      id-token: write   # required for OIDC
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1   # pin to a commit SHA
        with:
          attestations: true
```

### Rules

- Build in a separate job without `id-token: write`; only the publish job gets it.
- Pin third-party actions to a commit SHA.
- No `PYPI_API_TOKEN` secret is needed or wanted.
