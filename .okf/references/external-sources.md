---
type: Reference
title: "Primary external sources"
description: "Where to look things up: Dagger repo, docs and Python SDK, the 1.0 beta announcement, Daggerverse, the OKF spec and toolkit, and the external modules and MCP servers this repo depends on."
tags: [reference]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: dagger
    resource: https://github.com/dagger/dagger
    title: "dagger/dagger repository"
    author: team:dagger
  - id: docs
    resource: https://docs.dagger.io/getting-started/introduction/
    title: "Dagger documentation"
    author: team:dagger
  - id: python-sdk
    resource: https://github.com/dagger/python-sdk
    title: "dagger/python-sdk repository (the Python SDK module)"
    author: team:dagger
  - id: blog
    resource: https://dagger.io/blog/dagger-10-beta/
    title: "Dagger blog: Dagger 1.0 beta"
    author: team:dagger
  - id: okf
    resource: https://github.com/scaccogatto/okf-skills
    title: "okf-skills toolkit"
    author: human:scaccogatto
---

| Source | Use it for |
|--------|------------|
| [dagger/dagger](https://github.com/dagger/dagger)[^dagger] | `docs/current_docs/` read at the tag in use (`v1.0.0-beta.21`; `main` is ahead), `hack/designs/` (as-built designs, e.g. `workspace-agents.md`), `core/` for engine behaviour, `.changes/` release notes (`.changes/unreleased/` for the 1.0 betas), `skills/` |
| [docs.dagger.io](https://docs.dagger.io)[^docs] | rendered docs; the site may describe the `main` branch |
| [dagger/python-sdk](https://github.com/dagger/python-sdk)[^python-sdk] | the 1.0 Python SDK, itself a module (`github.com/dagger/python-sdk`, pinned in `dagger.lock`): README for migration rules, `python-sdk.dang` and `scope.dang` for what `dagger generate` writes |
| [Dagger 1.0 beta announcement](https://dagger.io/blog/dagger-10-beta/)[^blog] | what 1.0 changes and why |
| [daggerverse.dev](https://daggerverse.dev) | how published modules render |
| [kpenfound/dag github-issue](https://github.com/kpenfound/dag/tree/main/github-issue) | the GitHub issue/PR module every agent uses (pinned `b316e472`) |
| [Angular CLI MCP](https://angular.dev/ai/mcp), [python-lft-mcp](https://github.com/Agent-Hellboy/python-lft-mcp), [pypi-query-mcp-server](https://github.com/loonghao/pypi-query-mcp-server), [gcloud-mcp](https://github.com/googleapis/gcloud-mcp) | agent MCP servers |
| [spec-kit](https://github.com/github/spec-kit) | the method behind [Speck](/agents/speck.md) |
| [okf-skills](https://github.com/scaccogatto/okf-skills)[^okf] and its vendored OKF v0.2 spec | how to maintain this bundle; vendored in `.claude/skills/` |

The 1.0 concepts were written from the dagger/dagger repository at tag `v1.0.0-beta.21`
(`a7a2e64e`, 2026-10-23), dagger/python-sdk at v1.2.0 and `main` (`dfb18873`), the beta
announcement, and a migration session on that engine. The original bundle read the docs at tag
`v0.21.10` and `main` at `90f71a27` (2026-10-10), because dev.to and docs.dagger.io were not
reachable from the authoring environment.

[^dagger]: dagger/dagger repository
[^docs]: Dagger documentation
[^python-sdk]: dagger/python-sdk repository (the Python SDK module)
[^blog]: Dagger blog: Dagger 1.0 beta
[^okf]: okf-skills toolkit
