---
type: Architecture
title: "Module dependency graph"
description: "Which daggerverse modules depend on which (the clients of each scope in the root dagger.toml), and why most modules stay independent."
tags: [overview, architecture, dependencies]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Architecture section"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: decouple
    resource: https://github.com/telchak/daggerverse/commit/4a609bd383a11d7234e4f18dde149fe6f22779d7
    title: "refactor: decouple GCP modules from gcp-auth dependency"
    author: human:telchak
    last_modified: 2026-01-04T16:57:00+01:00
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (workspace), scope clients"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: goose-manifest
    resource: https://github.com/telchak/daggerverse/blob/main/goose/dagger-module.toml
    title: "goose/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Graph

```
oidc-token ──> gcp-auth
                 │ provides authenticated gcloud containers / access tokens
                 ├──> gcp-artifact-registry   (accepts gcloud: Container)
                 ├──> gcp-cloud-run           (accepts gcloud: Container)
                 ├──> gcp-vertex-ai           (accepts gcloud: Container)
                 └──> gcp-firebase            (accepts OIDC, SA key or access_token)

goose ──depends on──> gcp-auth, gcp-cloud-run, gcp-artifact-registry,
                      gcp-firebase, gcp-vertex-ai, health-check, github-issue

_agent_base (included, not a dependency) ──> angie, monty, daggie, speck, goose
  angie  ──> angular, github-issue   + Angular CLI MCP (node)
  monty  ──> python-build, github-issue + python-lft and pypi-query MCPs
  daggie ──> dagger-mcp, github-issue
  speck  ──> github-issue

standalone: angular, calver, dagger-mcp, health-check, oidc-token, python-build, semver
tests ──> all 17 modules above (scope clients ./<module>)
```

A module's dependencies are the `clients` of its scope in the root `dagger.toml`
(`[sdks.python.scopes.<module>] clients = [...]`), not a manifest field; `dagger generate`
turns each into a committed `<module>/clients/<dependency>`.[^workspace] See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).

Only `gcp-auth -> oidc-token` (`clients = ["./oidc-token"]`) is a dependency between plain
modules.[^readme] [^workspace] The GCP service modules used to depend on `gcp-auth`; since
2026-01-04 they instead accept a pre-authenticated `gcloud` container (or token), so a caller
authenticates once and passes the container to several modules.[^decouple] See the
[decision](/decisions/decouple-gcp-modules-from-gcp-auth.md).

Agents are the exception: the [Goose](/agents/goose.md) scope lists six local modules plus
`github-issue` as clients; Angie and Monty list their deterministic build module (`./angular`,
`./python-build`), Daggie lists `./dagger-mcp`, and Speck only `github-issue`.[^workspace]
`github-issue` is the external module `github.com/kpenfound/dag/github-issue`, pinned to commit
`b316e472d3de5bb0e54fe3991be68dc85e33ef38` in every agent's client reference.

`_agent_base` is not a client: every agent ships it through `include = ["../_agent_base"]` in its
`dagger-module.toml` (a runtime manifest, because the agents run on `legacyRuntime`) and installs
it as an editable local `uv` source. Goose has included it too since the 1.0
migration.[^goose-manifest] See [agent-base](/agents/agent-base.md).

The [tests module](/infrastructure/tests-module.md) scope lists all 17 modules as clients
(`./angular` ... `./speck`).[^workspace] All in-repo dependencies are local paths relative to the
root `dagger.toml`, see the [decision](/decisions/relative-paths-for-monorepo-dependencies.md).

[^readme]: Repository README, Architecture section
[^decouple]: refactor: decouple GCP modules from gcp-auth dependency
[^workspace]: dagger.toml (workspace), scope clients
[^goose-manifest]: goose/dagger-module.toml
