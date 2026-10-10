---
type: Dagger Module
title: "dagger-mcp"
description: "An MCP server, run as a privileged-nested Dagger service, that lets an LLM introspect the live Dagger engine schema, run GraphQL and read SDK guides."
resource: https://github.com/telchak/daggerverse/tree/main/dagger-mcp
tags: [module, mcp, dagger]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/src/dagger_mcp/main.py
    title: "dagger-mcp/src/dagger_mcp/main.py"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/README.md
    title: "dagger-mcp/README.md"
    author: human:telchak
    last_modified: 2026-03-01T14:43:35+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/dagger.json
    title: "dagger-mcp/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: server
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/src/dagger_mcp/server/main.py
    title: "dagger-mcp/src/dagger_mcp/server/main.py"
    author: human:telchak
    last_modified: 2026-02-24T11:00:27+01:00
  - id: pin
    resource: https://github.com/telchak/daggerverse/commit/a61586f7128c367fa3d401232c3a2e09ae786d95
    title: "fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
---

# Function

`server() -> Service`: a `python:3.13-slim` container running `server/main.py` with
`as_service(experimental_privileged_nesting=True)`.[^main]

# Tools exposed

| Tool | What it does |
|------|--------------|
| `learn_schema(type_name)` | introspects a GraphQL type and renders SDL (`sdl_renderer.py`) |
| `run_query(query)` | runs GraphQL against the live engine |
| `learn_sdk(sdk)` | returns `knowledge/{python,typescript,go}_sdk.md` |
| `dagger_version()` | engine version |

The server reaches the engine at `http://127.0.0.1:$DAGGER_SESSION_PORT/query` with
`DAGGER_SESSION_TOKEN` as basic-auth user, which privileged nesting provides.[^server]
It is built on `mcp.server.fastmcp.FastMCP`.

# Temporary `mcp<2` pin

`mcp` 2.0.0 (2026-07-28) removed `mcp.server.fastmcp`; unpinned, the server died at import and
Daggie's tests hung until the 20-minute step timeout. The install is pinned to `mcp<2` until the
server is ported to the 2.0 API.[^pin] See the [decision](/decisions/pin-mcp-below-2.md) and the
[agent CI timeout playbook](/playbooks/debug-agent-ci-timeout.md).

Consumed by [Daggie](/agents/daggie.md).

[^main]: dagger-mcp/src/dagger_mcp/main.py
[^server]: dagger-mcp/src/dagger_mcp/server/main.py
[^pin]: fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers
