---
type: Architecture
title: "Module dependency graph"
description: "Which daggerverse modules depend on which, and why most modules stay independent."
tags: [overview, architecture, dependencies]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Architecture section"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: decouple
    resource: https://github.com/telchak/daggerverse/commit/4a609bd383a11d7234e4f18dde149fe6f22779d7
    title: "refactor: decouple GCP modules from gcp-auth dependency"
    author: human:telchak
    last_modified: 2026-01-04T16:57:00+01:00
  - id: goose-json
    resource: https://github.com/telchak/daggerverse/blob/main/goose/dagger.json
    title: "goose/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: tests-json
    resource: https://github.com/telchak/daggerverse/blob/main/tests/dagger.json
    title: "tests/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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

_agent_base (included, not a dependency) ──> angie, monty, daggie, speck
  angie  ──> angular, github-issue   + Angular CLI MCP (node)
  monty  ──> python-build, github-issue + python-lft and pypi-query MCPs
  daggie ──> dagger-mcp, github-issue
  speck  ──> github-issue

standalone: angular, calver, dagger-mcp, health-check, oidc-token, python-build, semver
tests ──> every module above (relative paths)
```

Only `gcp-auth -> oidc-token` is a dependency between plain modules.[^readme] The GCP
service modules used to depend on `gcp-auth`; since 2026-01-04 they instead accept a
pre-authenticated `gcloud` container (or token), so a caller authenticates once and passes
the container to several modules.[^decouple] See the
[decision](/decisions/decouple-gcp-modules-from-gcp-auth.md).

Agents are the exception: [Goose](/agents/goose.md) declares six local module dependencies
plus `github-issue`,[^goose-json] and the coding agents depend on their deterministic
build module. `github-issue` is the external module
`github.com/kpenfound/dag/github-issue`, pinned to commit
`b316e472d3de5bb0e54fe3991be68dc85e33ef38` in every agent.

`_agent_base` is pulled in through the `include` field of `dagger.json`, not
`dependencies`, and installed as an editable local `uv` source. See
[agent-base](/agents/agent-base.md).

The [tests module](/infrastructure/tests-module.md) depends on every module through
relative paths (`../<module>`).[^tests-json] All in-repo dependencies use relative paths,
see the [decision](/decisions/relative-paths-for-monorepo-dependencies.md).

[^readme]: Repository README, Architecture section
[^decouple]: refactor: decouple GCP modules from gcp-auth dependency
[^goose-json]: goose/dagger.json
[^tests-json]: tests/dagger.json
