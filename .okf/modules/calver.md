---
type: Dagger Module
title: "calver"
description: "Calendar Versioning: generate date-based version strings, optionally auto-incrementing MICRO from git tags."
resource: https://github.com/telchak/daggerverse/tree/main/calver
tags: [module, versioning]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
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
    last_modified: 2026-01-20T20:17:15+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/calver/dagger.json
    title: "calver/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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

# History

CalVer was the repository's release scheme until 2026-03-05 (a dated GitHub release
listing all module versions); it was replaced by per-module semver tags. See
[release process](/infrastructure/release-process.md). The module is still published and tested
by `tests calver` (no credentials).[^module-readme]

[^main]: calver/src/calver/main.py
[^module-readme]: calver/README.md
