---
type: Decision
title: "Per-module semver tags instead of a repo CalVer release"
description: "Each module is released as <module>/vX.Y.Z from Conventional Commits; the repo-wide CalVer GitHub release was dropped."
tags: [decision, release, versioning]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: calver
    resource: https://github.com/telchak/daggerverse/commit/ff38e7a76d21733f4842760efea26ad874a8e507
    title: "refactor: redesign release workflow with calver-based releases"
    author: human:telchak
    last_modified: 2025-12-31T17:53:51+01:00
  - id: drop
    resource: https://github.com/telchak/daggerverse/commit/d44547db1c67ff39bcb75b79a025b688226311ab
    title: "fix: improve daggerverse publishing (release tags)"
    author: human:telchak
    last_modified: 2026-03-05T14:21:19+01:00
  - id: semver-add
    resource: https://github.com/telchak/daggerverse/commit/e1a47e59ddf83d080170481b653af075c669a4f9
    title: "feat: add semver module and automatic release workflow"
    author: human:telchak
    last_modified: 2025-12-31T10:33:26+01:00
---

# Timeline

- 2025-12-31: [semver](/modules/semver.md) module and auto release added;[^semver-add] same day a
  CalVer-based release (`vYYYY.MM.MICRO`, later `vYYYY.MM.DD`) was layered on top.[^calver]
- 2026-03-05: the CalVer GitHub release step was removed; only per-module tags remain, since the
  Daggerverse indexes `<module>/vX.Y.Z` tags.[^drop]

See [release process](/infrastructure/release-process.md).

[^calver]: refactor: redesign release workflow with calver-based releases
[^drop]: fix: improve daggerverse publishing (release tags)
[^semver-add]: feat: add semver module and automatic release workflow
