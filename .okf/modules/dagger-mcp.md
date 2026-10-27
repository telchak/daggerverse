---
type: Dagger Module
title: "dagger-mcp"
description: "An MCP server, packaged as a Dagger-in-Dagger container and service, that lets an LLM introspect the live Dagger engine schema, run GraphQL and read SDK guides."
resource: https://github.com/telchak/daggerverse/tree/main/dagger-mcp
tags: [module, mcp, dagger]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/src/dagger_mcp/main.py
    title: "dagger-mcp/src/dagger_mcp/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/README.md
    title: "dagger-mcp/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/dagger-module.toml
    title: "dagger-mcp/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: server
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/src/dagger_mcp/server/main.py
    title: "dagger-mcp/src/dagger_mcp/server/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: knowledge
    resource: https://github.com/telchak/daggerverse/blob/main/dagger-mcp/src/dagger_mcp/server/knowledge/python_sdk.md
    title: "dagger-mcp/src/dagger_mcp/server/knowledge/python_sdk.md (and go_sdk.md, typescript_sdk.md)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/main.py
    title: "daggie/src/daggie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: mcp-stdio
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/mcp_stdio.py
    title: "_agent_base/src/agent_base/mcp_stdio.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: tests
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/dagger_agent.py
    title: "tests/src/tests/dagger_agent.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: pin
    resource: https://github.com/telchak/daggerverse/commit/a61586f7128c367fa3d401232c3a2e09ae786d95
    title: "fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
---

# Functions

| Function | Returns |
|----------|---------|
| `container()` | `Container`: `python:3.13-slim`, `pip install "mcp<2" httpx`, the server code (`src/dagger_mcp/server`) at `/app`, default args `python main.py` |
| `server()` | `Service`: `container().as_service()` |

`container()` was added in the Dagger 1.0 migration and `server()` builds on it. The 0.x
`as_service(experimental_privileged_nesting=True)` is gone: Dagger-in-Dagger is on by default in
1.0.[^main]

# Tools exposed

| Tool | What it does |
|------|--------------|
| `learn_schema(type_name)` | introspects a GraphQL type and renders SDL (`sdl_renderer.py`) |
| `run_query(query)` | runs GraphQL against the live engine |
| `learn_sdk(sdk)` | returns `knowledge/{python,typescript,go}_sdk.md` |
| `dagger_version()` | engine version |

The server reaches the engine at `http://127.0.0.1:$DAGGER_SESSION_PORT/query` with
`DAGGER_SESSION_TOKEN` as basic-auth user, which Dagger-in-Dagger provides.[^server]
It is built on `mcp.server.fastmcp.FastMCP`. The SDK guides describe the 1.0 layout
(`dagger-module.toml`, the scope in `dagger.toml`) and the `Workspace` argument and check
patterns.[^knowledge]

# How agents run it

Consumed by [Daggie](/agents/daggie.md). `LLM.with_mcp_server` hangs on the second LLM step in
beta.21, so Daggie does not attach `server()`: it wraps `container()` in an `McpServer`
(`command=["python", "main.py"]`, `dagger_access=True` to keep Dagger-in-Dagger, `live=True` so
answers are never cached).[^daggie] The server's tools are listed in the system prompt, and the
agent's `mcp` tool runs a one-shot stdio driver in that container for each call.[^mcp-stdio] See
the [MCP exec driver decision](/decisions/mcp-exec-driver.md) and
[known issues](/dagger/known-issues-1-0-beta.md). The module README still shows the
`with_mcp_server("dagger", dag.dagger_mcp().server())` wiring.[^module-readme]

The tests check that `container()` holds `/app/main.py` and only build `server()`, since the
service is lazy.[^tests]

# Temporary `mcp<2` pin

`mcp` 2.0.0 (2026-07-28) removed `mcp.server.fastmcp`; unpinned, the server died at import and
Daggie's tests hung until the 20-minute step timeout. The install in `container()` is pinned to
`mcp<2` until the server is ported to the 2.0 API.[^pin] See the
[decision](/decisions/pin-mcp-below-2.md) and the
[agent CI timeout playbook](/playbooks/debug-agent-ci-timeout.md).

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: dagger-mcp/src/dagger_mcp/main.py
[^module-readme]: dagger-mcp/README.md
[^manifest]: dagger-mcp/dagger-module.toml
[^server]: dagger-mcp/src/dagger_mcp/server/main.py
[^knowledge]: dagger-mcp/src/dagger_mcp/server/knowledge/python_sdk.md (and go_sdk.md, typescript_sdk.md)
[^daggie]: daggie/src/daggie/main.py
[^mcp-stdio]: _agent_base/src/agent_base/mcp_stdio.py
[^tests]: tests/src/tests/dagger_agent.py
[^pin]: fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers
