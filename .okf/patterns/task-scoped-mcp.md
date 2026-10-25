---
type: Design Pattern
title: "Task-scoped MCP servers"
description: "Agents attach MCP servers (and experimental MCP tools) only to the entrypoints that benefit, list their tools in the system prompt and call them through an mcp tool."
tags: [agent, mcp, pattern]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/main.py
    title: "daggie/src/daggie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: goose
    resource: https://github.com/telchak/daggerverse/blob/main/goose/src/goose/main.py
    title: "goose/src/goose/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: mcp-stdio
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/mcp_stdio.py
    title: "agent_base/mcp_stdio.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: perf
    resource: https://github.com/telchak/daggerverse/commit/1f77e994938ca92059721a5a895454e3f8da3f36
    title: "feat: Improve CI caching, agent reliability, and MCP startup performance"
    author: human:telchak
    last_modified: 2026-02-21T18:58:15+01:00
---

# Per agent

| Agent | Table | MCP on | MCP off |
|-------|-------|--------|---------|
| Angie | `_TASK_MCP_TOOLS` (experimental `ng mcp` tools per task) | assist (build,test,modernize), build (build), upgrade (modernize) | review, write_tests, suggest_fix[^angie] |
| Daggie | `_TASK_MCP_TOOLS` | assist, explain, debug | review[^daggie] |
| Goose | `_TASK_NEEDS_MCP` | assist, troubleshoot, upgrade | deploy, review, suggest_fix[^goose] |
| Monty | none | both servers on every task | suggest_fix |
| Speck | none | | always (no MCP) |

Rationale recorded in Angie's code: for review "MCP can't see files and confuses the LLM", and
write_tests "just needs to read code and write test files". MCP servers are containers that must
install before they answer, so skipping them also cuts time.[^perf]

# How a server is attached (Dagger 1.0)

An `McpServer` names a container (with Python 3) and the server's stdio command, plus `live`
(never cache answers: gcloud, pypi, dagger) and `dagger_access` (Dagger-in-Dagger, only for
dagger-mcp).[^mcp-stdio] Because `LLM.with_mcp_server` hangs on the second step in
v1.0.0-beta.21, `mcp_stdio.attach` instead:

1. runs `tools/list` once through a one-shot driver and appends a `## MCP Servers` catalog
   (tool names, argument names, descriptions cut at 300 characters) to the system prompt;
2. leaves the agent's `mcp(server, tool, arguments)` tool in the tool set, which runs one
   `tools/call` per request in the server's container and returns its text.

A task without servers gets no catalog, and `mcp` is excluded from its tools. Setting
`mcp_stdio.ENGINE_MCP = True` goes back to `with_mcp_server` once the engine bug is fixed. See
the [decision](/decisions/mcp-exec-driver.md) and [Dagger LLM and MCP](/dagger/llm-and-mcp.md).

[^angie]: angie/src/angie/main.py
[^daggie]: daggie/src/daggie/main.py
[^goose]: goose/src/goose/main.py
[^mcp-stdio]: agent_base/mcp_stdio.py
[^perf]: feat: Improve CI caching, agent reliability, and MCP startup performance
