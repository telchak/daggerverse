---
type: Reference
title: "Upcoming: Dagger 1.0 workspaces (dagger.toml)"
description: "Dagger's main branch splits dagger.json into dagger-module.toml (module manifest) and dagger.toml (workspace config), with migrate commands; not released as of v0.21.10."
tags: [dagger, future, migration]
status: draft
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: migrate
    resource: https://github.com/dagger/dagger/blob/main/docs/current_docs/config/migrate-dagger-json.mdx
    title: "Dagger docs source: Migrate from dagger.json (main branch)"
    author: team:dagger
    last_modified: 2026-10-10T14:22:01Z
  - id: toml
    resource: https://github.com/dagger/dagger/blob/main/docs/current_docs/reference/config-files/dagger-toml.mdx
    title: "Dagger docs source: dagger.toml reference (main branch)"
    author: team:dagger
    last_modified: 2026-10-10T14:22:01Z
---

On dagger/dagger `main` (2026-10-10), docs describe Dagger 1.0 splitting the two roles of
`dagger.json`:[^migrate]

| Role | 0.x | 1.0 |
|------|-----|-----|
| module manifest | `dagger.json` | `dagger-module.toml` |
| workspace config | `dagger.json` | `dagger.toml`[^toml] |

- 1.0 can still load `dagger.json` in both roles; migration is optional at first.
- `dagger workspace migrate` converts a workspace (an `sdk` module goes to `.dagger/modules/<name>`;
  toolchains become installed modules, customizations become settings; `blueprint` cannot migrate)
  and writes `.dagger/migration-report.md`.
- `dagger module migrate ./path` migrates one module.
- Coding agents must pass `-y` or `--no-apply` explicitly.

**Impact on this repo when 1.0 ships:** 17 module `dagger.json` files, Renovate's `engineVersion`
regex, CI's `find ... -name dagger.json` discovery and validation, and the `include`-based
agent-base sharing all assume `dagger.json`. Plan a migration and update
[CI](/infrastructure/ci-pipeline.md), [Renovate](/infrastructure/renovate.md) and
[module anatomy](/conventions/module-anatomy.md) together.

Draft: describes unreleased upstream work that may change before release.

[^migrate]: Dagger docs source: Migrate from dagger.json (main branch)
[^toml]: Dagger docs source: dagger.toml reference (main branch)
