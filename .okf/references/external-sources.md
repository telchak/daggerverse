---
type: Reference
title: "Primary external sources"
description: "Where to look things up: Dagger repo and docs, Daggerverse, the OKF spec and toolkit, and the external modules and MCP servers this repo depends on."
tags: [reference]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: dagger
    resource: https://github.com/dagger/dagger
    title: "dagger/dagger repository"
    author: team:dagger
  - id: docs
    resource: https://docs.dagger.io/getting-started/introduction/
    title: "Dagger documentation"
    author: team:dagger
  - id: okf
    resource: https://github.com/scaccogatto/okf-skills
    title: "okf-skills toolkit"
    author: human:scaccogatto
---

| Source | Use it for |
|--------|------------|
| [dagger/dagger](https://github.com/dagger/dagger)[^dagger] | `.changes/<version>.md` release notes, `docs/current_docs/` (read at the tag matching `engineVersion`, `main` is ahead), `skills/` |
| [docs.dagger.io](https://docs.dagger.io)[^docs] | rendered docs; the site may describe the `main` branch |
| [daggerverse.dev](https://daggerverse.dev) | how published modules render |
| [kpenfound/dag github-issue](https://github.com/kpenfound/dag/tree/main/github-issue) | the GitHub issue/PR module every agent uses (pinned `b316e472`) |
| [Angular CLI MCP](https://angular.dev/ai/mcp), [python-lft-mcp](https://github.com/Agent-Hellboy/python-lft-mcp), [pypi-query-mcp-server](https://github.com/loonghao/pypi-query-mcp-server), [gcloud-mcp](https://github.com/googleapis/gcloud-mcp) | agent MCP servers |
| [spec-kit](https://github.com/github/spec-kit) | the method behind [Speck](/agents/speck.md) |
| [okf-skills](https://github.com/scaccogatto/okf-skills)[^okf] and its vendored OKF v0.2 spec | how to maintain this bundle; vendored in `.claude/skills/` |

The authoring environment for this bundle could not reach dev.to or docs.dagger.io; Dagger docs
were read from the dagger/dagger repository instead (tag `v0.21.10`, and `main` at
`90f71a27`, 2026-10-10).

[^dagger]: dagger/dagger repository
[^docs]: Dagger documentation
[^okf]: okf-skills toolkit
