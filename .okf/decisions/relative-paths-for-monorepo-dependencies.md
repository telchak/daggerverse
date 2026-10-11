---
type: Decision
title: "Use relative paths for in-repo module dependencies"
description: "In-repo dagger.json dependencies use ../<module> paths, not github.com URLs; tried and reverted on 2026-01-04."
tags: [decision, dependencies, monorepo]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: urls
    resource: https://github.com/telchak/daggerverse/commit/5a915ec7400bf11e8d4c9a8cbebf42e9065d75c8
    title: "refactor: use repository URLs for module dependencies"
    author: human:telchak
    last_modified: 2026-01-04T11:56:08+01:00
  - id: revert
    resource: https://github.com/telchak/daggerverse/commit/48430642f54dd67f92575e56ea7fdc2a1c791de3
    title: "fix: revert to relative paths for all monorepo dependencies"
    author: human:telchak
    last_modified: 2026-01-04T12:53:14+01:00
  - id: oidc-try
    resource: https://github.com/telchak/daggerverse/commit/e5ed5042083135fc709faf31634c3aa5225b3553
    title: "fix(gcp-auth): revert to local path for oidc-token dependency"
    author: human:telchak
    last_modified: 2026-01-06T22:49:27+01:00
---

# Context

On 2026-01-04 every `dagger.json` was switched to `github.com/telchak/daggerverse/<module>` so
dependencies would resolve from the remote when consumed from the Daggerverse.[^urls]

# Decision

Reverted the same day to relative paths:[^revert]

- Dagger fetched the dependency from the remote, where the latest code may not be pushed yet.
- Network and auth problems caused silent failures.
- Local and remote code could diverge.

Dagger resolves relative paths correctly for published modules too. The same back-and-forth
happened for `gcp-auth -> oidc-token` on 2026-01-06.[^oidc-try] External modules
(`kpenfound/dag/github-issue`) stay pinned by commit.

[^urls]: refactor: use repository URLs for module dependencies
[^revert]: fix: revert to relative paths for all monorepo dependencies
[^oidc-try]: fix(gcp-auth): revert to local path for oidc-token dependency
