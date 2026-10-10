---
type: Configuration
title: "Renovate configuration"
description: "Renovate keeps the Dagger engine version in sync across dagger.json, CI and README, groups it, and never bumps uv_build."
tags: [dependencies, renovate]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: renovate
    resource: https://github.com/telchak/daggerverse/blob/main/renovate.json
    title: "renovate.json"
    author: human:telchak
    last_modified: 2026-04-14T15:45:03+02:00
  - id: label
    resource: https://github.com/telchak/daggerverse/commit/67f7080c002ec91627d14d3b1773d41382d3485e
    title: "fix(renovate): capture full semver in runner label regex"
    author: human:telchak
    last_modified: 2026-04-14T15:45:03+02:00
  - id: tests
    resource: https://github.com/telchak/daggerverse/commit/24a3b0eaf691b0f8e8a8bf1c18e66eea5a90c434
    title: "fix(renovate): include tests/ directory in dagger engine version updates"
    author: human:telchak
    last_modified: 2026-02-28T20:03:42+01:00
---

# Custom managers (`dagger/dagger` github-releases)

| Where | Regex target |
|-------|--------------|
| every `dagger.json` | `"engineVersion": "v<ver>"` |
| `.github/workflows/*.yml` | `DAGGER_VERSION: "<ver>"` |
| `.github/workflows/*.yml` | `runs-on: dagger-v<ver>` (self-hosted runner label) |
| `README.md` files | the `Dagger-v<ver>-` badge |

All four are grouped as **"dagger engine"**, so one PR bumps engine, CLI, runner label and
badges together.[^renovate] The runner-label regex was fixed to capture the full semver on
2026-04-14,[^label] and `tests/` was included on 2026-02-28.[^tests]

# Rules

- `uv_build` / `uv-build` updates are disabled: the version is dictated by Dagger's Python SDK
  template.
- `examples/`, `node_modules`, fixtures and similar paths are ignored.

An engine bump also requires a matching self-hosted runner image; see
[upgrade the Dagger engine](/playbooks/upgrade-dagger-engine.md).

[^renovate]: renovate.json
[^label]: fix(renovate): capture full semver in runner label regex
[^tests]: fix(renovate): include tests/ directory in dagger engine version updates
