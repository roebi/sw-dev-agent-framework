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

## References

- `references/semver.md` - semver rules and examples
- `references/trusted-publishing.md` - PyPI OIDC workflow setup
