---
type: Convention
title: "Conventional Commits"
description: "Commit messages follow Conventional Commits with the module as scope, because the release job derives version bumps from them."
tags: [convention, git, release]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Commit Messages"
    author: human:telchak
    last_modified: 2026-03-05T15:49:35+01:00
  - id: semver
    resource: https://github.com/telchak/daggerverse/blob/main/semver/src/semver/main.py
    title: "semver/src/semver/main.py"
    author: human:telchak
    last_modified: 2026-03-01T19:35:32+01:00
---

Format: `<type>(<scope>): <description>`, scope = module name (`feat(gcp-firebase): ...`,
`fix(daggie,monty): ...`).[^contributing]

| Type | Bump |
|------|------|
| `feat` | minor |
| `fix`, `perf`, `refactor` | patch |
| `docs`, `test`, `chore`, `ci`, `build`, `style` | patch through the default bump |
| `feat!:` or `BREAKING CHANGE` | major |

Write `BREAKING CHANGE` only when meant: the parser matches it anywhere in a line, body
included.[^semver] And bump detection is repository-wide, see [semver](/modules/semver.md).

PR guidance: one module or concern per PR, tests in `tests/`, README updated when the public API
changes. Branch from `main`.

[^contributing]: Contributing guide, Commit Messages
[^semver]: semver/src/semver/main.py
