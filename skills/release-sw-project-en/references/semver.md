# Semantic Versioning - Rules and Examples

Version format: `MAJOR.MINOR.PATCH` (see https://semver.org/spec/v2.0.0.html).

| Change | Bump | Example |
|---|---|---|
| Incompatible API or behaviour change (`BREAKING CHANGE:` in commit body, or `!` after the type, e.g. `feat!:`) | MAJOR | 1.4.2 -> 2.0.0 |
| New backwards-compatible feature (`feat:`) | MINOR | 1.4.2 -> 1.5.0 |
| Backwards-compatible bug fix only (`fix:`) | PATCH | 1.4.2 -> 1.4.3 |
| `docs:`, `test:`, `chore:`, `ci:`, `refactor:` only | no release needed | - |

## Rules

- The highest-ranked change since the last tag decides the bump.
- A bump resets the lower parts: MINOR bump sets PATCH to 0; MAJOR bump sets MINOR and PATCH to 0.
- While MAJOR is 0 (`0.y.z`), the API is unstable; breaking changes bump MINOR.
- Never re-use or move a published version tag. A broken release is fixed by a new PATCH release.
- Software version tags use the form `vX.Y.Z`.

## Examples

```
v1.2.0..HEAD: fix: handle empty file          -> v1.2.1
v1.2.0..HEAD: feat: add --output flag         -> v1.3.0
v1.2.0..HEAD: feat!: drop Python 3.11 support -> v2.0.0
```
