---
type: Decision
title: "Use relative paths for in-repo module dependencies"
description: "In-repo module dependencies use local paths (0.x: ../<module> in dagger.json; 1.0: ./<module> scope clients in dagger.toml), not github.com URLs; tried and reverted on 2026-01-04."
tags: [decision, dependencies, monorepo]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
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
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (workspace), scope clients"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: toml-ref
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/config-files/dagger-toml.mdx
    title: "Dagger docs: dagger.toml reference (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: loader
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/sdk/src/dagger/client/_load.py
    title: "Python SDK client loader (vendored in gcp-auth/sdk)"
    author: team:dagger
    last_modified: 2026-10-24T22:00:00Z
  - id: target
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/clients/oidc-token/src/dagger_clients/oidc_token/_target.py
    title: "gcp-auth's generated oidc-token client target"
    author: team:dagger
    last_modified: 2026-10-24T22:00:00Z
---

# Context

On 2026-01-04 every `dagger.json` was switched to `github.com/telchak/daggerverse/<module>` so
dependencies would resolve from the remote when consumed from the Daggerverse.[^urls]

# Decision

Reverted the same day to relative paths:[^revert]

- Dagger fetched the dependency from the remote, where the latest code may not be pushed yet.
- Network and auth problems caused silent failures.
- Local and remote code could diverge.

Dagger (0.x) resolves relative paths correctly for published modules too. The same back-and-forth
happened for `gcp-auth -> oidc-token` on 2026-01-06.[^oidc-try] External modules
(`kpenfound/dag/github-issue`) stay pinned by commit.

# Dagger 1.0 consequence

The dependencies moved from each module's `dagger.json` to the `clients` of its scope in the
root `dagger.toml`, and they stay local paths: `./oidc-token` for `gcp-auth`, `./<module>` for
the agents and `tests`.[^workspace] The prefix changed from `../` to `./` because client paths
are relative to the directory holding `dagger.toml`, and a bare `<module>` is not a local
path.[^toml-ref] `github-issue` is still pinned by commit in its client reference
(`github.com/kpenfound/dag/github-issue@b316e472...`).[^workspace]

A generated client records a local dependency as a workspace path (`REF = "/oidc-token"`),[^target]
and the SDK's loader leaves it to the engine, which "resolves it in the tree of the module whose
code runs".[^loader] So a `gcp-auth` installed from Git should load `oidc-token` from the same
repository and commit; this is read from the code, not yet seen on a published 1.0 release.

[^urls]: refactor: use repository URLs for module dependencies
[^revert]: fix: revert to relative paths for all monorepo dependencies
[^oidc-try]: fix(gcp-auth): revert to local path for oidc-token dependency
[^workspace]: dagger.toml (workspace), scope clients
[^toml-ref]: Dagger docs: dagger.toml reference (v1.0.0-beta.21)
[^loader]: Python SDK client loader (vendored in gcp-auth/sdk)
[^target]: gcp-auth's generated oidc-token client target
