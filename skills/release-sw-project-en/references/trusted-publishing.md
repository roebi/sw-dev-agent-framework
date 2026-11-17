# PyPI Trusted Publishing (OIDC) - Setup

Trusted Publishing lets a GitHub Actions workflow publish to PyPI without
an API token. PyPI trusts a short-lived OIDC token issued by GitHub for a
specific repository, workflow file and environment.

## One-time setup on PyPI

1. Open https://pypi.org/manage/account/publishing/ (new project) or the
   project's "Publishing" settings (existing project).
2. Add a GitHub publisher with:
   - Owner: `<github-owner>`
   - Repository: `<repo-name>`
   - Workflow name: `release.yml`
   - Environment: `pypi`

## One-time setup on GitHub

Create the environment `pypi` under Settings -> Environments. Optionally
add required reviewers so every publish needs a manual approval.

## Workflow

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

## Rules

- Build in a separate job without `id-token: write`; only the publish job gets it.
- Pin third-party actions to a commit SHA.
- No `PYPI_API_TOKEN` secret is needed or wanted.
