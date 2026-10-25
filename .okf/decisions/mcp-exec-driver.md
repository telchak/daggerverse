---
type: Decision
title: "Call MCP servers through a one-shot stdio driver (temporary)"
description: "Because LLM.with_mcp_server hangs on the second LLM step in Dagger v1.0.0-beta.21, agents list MCP tools in the system prompt and call them through their own mcp tool, one exec per request."
tags: [decision, mcp, agents, temporary, workaround]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: mcp-stdio
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/mcp_stdio.py
    title: "_agent_base/src/agent_base/mcp_stdio.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: mcp-go
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/mcp.go
    title: "Dagger engine: MCP sessions (core/mcp.go, syncMCPSessions)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: services-go
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/services.go
    title: "Dagger engine: service start and reuse (core/services.go, startWithKey)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: session
    resource: local migration session on a Windows 11 host, 2026-10-24
    title: "Reproduction with a minimal FastMCP server and the Angular CLI MCP, scripted mock LLM"
    author: claude-code/2.1.310
---

# Context

Ported to 1.0, Angie's `assist` hung after its first tool call, at "start mcp server: angular".
A minimal FastMCP server reproduced it; Dagger-in-Dagger settings made no difference.[^session]
Cause: `syncMCPSessions` stores the dialed sessions on a transient clone, so every LLM step dials
the server again,[^mcp-go] and `startWithKey` finds the service already running under the same
key and returns it without attaching the new stdin and stdout,[^services-go] so the second
`initialize` is never answered.

# Decision (2026-10-24)

Keep MCP out of the engine's LLM loop until it is fixed. `_agent_base/mcp_stdio.py`:[^mcp-stdio]

- `McpServer`: a container with Python 3, the server's stdio command, `live` (add a unique env
  var so calls reading live state are never cached) and `dagger_access` (Dagger-in-Dagger, only
  for dagger-mcp; the others run with `disable_dagger_in_dagger=True`).
- A standard-library driver, run in the server's container per request: start the server, send
  `initialize`, `notifications/initialized` and one request, print the answer, kill it (120 s
  timeout).
- `catalog()` lists each server's tools (`tools/list`) in a `## MCP Servers` section of the
  system prompt; each agent exposes `mcp(server, tool, arguments="{}")`, which runs `tools/call`
  and returns its text, raising on `isError`.

# Consequences

- Each call starts the server again: slower calls and no server-side session state, which these
  servers do not need. Server containers need `python3`.
- The catalog adds prompt tokens; descriptions are cut at 300 characters.
- Verified on 1.0 with a scripted mock LLM: Angie's catalog listed the 9 Angular MCP tools, the
  `mcp` call answered in 1.7 s, and the loop continued to a `writeFile` edit and a final reply.[^session]

# Exit

When an engine release keeps MCP sessions across steps: set `mcp_stdio.ENGINE_MCP = True` (MCP
servers go back to `LLM.with_mcp_server` and the `mcp` tool is hidden), run the agent CI, then
remove the driver. The bug is not reported upstream yet. See
[known issues](/dagger/known-issues-1-0-beta.md) and [task-scoped MCP](/patterns/task-scoped-mcp.md).

[^mcp-stdio]: _agent_base/src/agent_base/mcp_stdio.py
[^mcp-go]: Dagger engine: MCP sessions (core/mcp.go, syncMCPSessions)
[^services-go]: Dagger engine: service start and reuse (core/services.go, startWithKey)
[^session]: Reproduction with a minimal FastMCP server and the Angular CLI MCP, scripted mock LLM
