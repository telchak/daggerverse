# Dagger MCP

MCP server for Dagger engine introspection — learn schema, run GraphQL queries, and get SDK guidance. Designed to be consumed by AI agents running inside Dagger.

## Installation

```bash
# Install into your workspace (dagger.toml)
dagger module install github.com/telchak/daggerverse/dagger-mcp@<version>

# Or add it as a dependency of your own module, from the module's directory
dagger module client add github.com/telchak/daggerverse/dagger-mcp@<version> --sdk=python
```

## Functions

| Function | Description |
|----------|-------------|
| `container` | The server's container (`python:3.13-slim`, server code in `/app`, default args `python main.py`), to run the stdio server yourself |
| `server` | The MCP server as a Dagger service (stdio transport): `container().as_service()` |

## How It Works

The module builds a container with a [FastMCP](https://pypi.org/project/mcp/) server that connects to the Dagger engine's GraphQL API through Dagger-in-Dagger, which Dagger 1.0 enables for services by default. When started as a service, the container receives `DAGGER_SESSION_PORT` and `DAGGER_SESSION_TOKEN` environment variables, which the MCP server uses to query the engine.

### MCP Tools Provided

| Tool | Description |
|------|-------------|
| `learn_schema(type_name)` | Introspect any type from the Dagger GraphQL schema (returns SDL) |
| `run_query(query)` | Execute a GraphQL query against the live Dagger engine |
| `learn_sdk(sdk)` | Get SDK-specific translation guidance (`python`, `typescript`, `go`) |
| `dagger_version()` | Get the running Dagger engine version |

## Usage

### As a Dependency (Agent Integration)

Add `dagger-mcp` as a client (dependency) of your agent module, from the agent's directory:

```shell
dagger module client add github.com/telchak/daggerverse/dagger-mcp@<version> --sdk=python
```

This records the client in your workspace's `dagger.toml` and regenerates the agent's bindings, so `dag.dagger_mcp()` is available.

Then wire it into your LLM as an MCP server:

```python
from dagger import dag

# Get the MCP service
mcp_service = dag.dagger_mcp().server()

# Pass to an LLM with MCP support
llm = dag.llm().with_mcp_server("dagger", mcp_service)
```

> **Dagger v1.0.0-beta.21:** an LLM with `with_mcp_server` hangs on its second step (the engine dials the server again for each step and gets the running service back without its stdio, [dagger/dagger#14856](https://github.com/dagger/dagger/issues/14856)). Until that is fixed, [Daggie](../daggie/) runs one MCP request per exec in `dag.dagger_mcp().container()` and exposes the server's tools through its own `mcp` tool; see [`_agent_base/src/agent_base/mcp_stdio.py`](../_agent_base/src/agent_base/mcp_stdio.py).

### CLI

```bash
# Verify the module loads
dagger api functions -m github.com/telchak/daggerverse/dagger-mcp

# The server function returns a Service — it's meant to be consumed by
# other modules, not called directly from the CLI
```

### Python Example

```python
from dagger import dag

# Use in an AI agent pipeline
llm = (
    dag.llm()
    .with_mcp_server("dagger", dag.dagger_mcp().server())
    .with_prompt("Use learn_schema to explore the Container type")
)
result = await llm.loop().last_reply()  # last_reply() alone does not run the loop
```

## SDK Knowledge

The `learn_sdk` tool provides translation guides for converting GraphQL API patterns into SDK-specific code:

- **Python** — `@object_type`, `@function`, `dag.container()`, async/await, type annotations
- **TypeScript** — `@object()`, `@func()`, decorators, camelCase methods
- **Go** — struct methods, `dag.Container()`, pointer receivers, comment annotations

## Architecture

```
dagger-mcp/
  dagger-module.toml           # module manifest (generated code in sdk/ and clients/ is committed)
  src/dagger_mcp/
    main.py                    # Dagger module — container() and server()
    server/
      main.py                  # FastMCP server (runs inside container)
      sdl_renderer.py          # GraphQL introspection → SDL converter
      knowledge/
        python_sdk.md           # Python SDK translation guide
        typescript_sdk.md       # TypeScript SDK translation guide
        go_sdk.md               # Go SDK translation guide
```

## Acknowledgements

This module is heavily inspired by [vito/daggerverse/mcp](https://github.com/vito/daggerverse/tree/main/mcp) — a Go implementation of the same concept. This Python equivalent uses FastMCP instead of Go's MCP SDK and adds multi-SDK knowledge (Python, TypeScript, Go) rather than Go-only guidance.

## License

Apache 2.0
