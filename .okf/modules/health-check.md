---
type: Dagger Module
title: "health-check"
description: "Container health checks (HTTP, TCP, exec, readiness) using Dagger service bindings."
resource: https://github.com/telchak/daggerverse/tree/main/health-check
tags: [module, testing]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/health-check/src/health_check/main.py
    title: "health-check/src/health_check/main.py"
    author: human:telchak
    last_modified: 2026-01-20T20:17:15+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/health-check/README.md
    title: "health-check/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/health-check/dagger-module.toml
    title: "health-check/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Functions

| Function | Mechanism |
|----------|-----------|
| `http(container, port, path, timeout)` | binds the container as a service, `curl` from `curlimages/curl` |
| `tcp(container, port, timeout)` | `nc` from alpine |
| `exec(container, command)` | runs a command in the container |
| `ready(container, port, endpoint?, timeout)` | HTTP if `endpoint` given, TCP otherwise |

Every function returns the input `Container` when healthy, so checks chain into a pipeline
(`build -> health_check.http -> publish`).[^main] [Goose](/agents/goose.md) wraps `http` and
`tcp` as agent tools (`check_http_health`, `check_tcp_health`).

They are container probes, not Dagger `@check` functions.[^main] The README's CLI form is
`dagger api call health-check http --container=... --port=8080 --path=/health`.[^module-readme]

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: health-check/src/health_check/main.py
[^module-readme]: health-check/README.md
[^manifest]: health-check/dagger-module.toml
