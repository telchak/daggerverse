---
type: Dagger Module
title: "calver"
description: "Calendar Versioning: generate date-based version strings, optionally auto-incrementing MICRO from git tags."
resource: https://github.com/telchak/daggerverse/tree/main/calver
tags: [module, versioning]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/calver/src/calver/main.py
    title: "calver/src/calver/main.py"
    author: human:telchak
    last_modified: 2026-02-17T10:31:33+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/calver/README.md
    title: "calver/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/calver/dagger-module.toml
    title: "calver/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: tests
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/main.py
    title: "tests/src/tests/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Functions

| Function | Returns | Notes |
|----------|---------|-------|
| `generate(format="YYYY.MM.DD", micro=0, source?, push_tag=false, github_token?)` | `str` | Date tokens (`YYYY`, `MM`, `0M`, `DD`, ...) plus an optional `MICRO` placeholder |

Behaviour:[^main]

- With `source` and a `MICRO` token, it scans the repo's tags (`source.as_git().tags()`)
  for the same pattern and uses the highest MICRO + 1.
- If HEAD already carries a tag matching the pattern, that tag is returned instead,
  which keeps a re-run on the same commit idempotent.
- `push_tag` creates and pushes the tag using `github_token` (an `alpine/git` container).
- Dates are taken in UTC.

Prefixes go in the format itself (`v.YYYY.MM.MICRO`); the README's CLI form is
`dagger api call calver generate --format="YYYY.0M.0D"`.[^module-readme]

# History

CalVer was the repository's release scheme until 2026-03-05 (a dated GitHub release
listing all module versions); it was replaced by per-module semver tags. See
[release process](/infrastructure/release-process.md). The module is still published and tested
by `dagger api call -m ./tests calver` (no credentials), also wrapped as the `check_calver`
check of `dagger check -m ./tests`.[^tests]

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: calver/src/calver/main.py
[^module-readme]: calver/README.md
[^manifest]: calver/dagger-module.toml
[^tests]: tests/src/tests/main.py
