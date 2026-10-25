---
type: Playbook
title: "Debug an agent test that times out in CI"
description: "An agent CI job that dies at exactly 20 minutes with no traceback usually means a hung MCP session, an agent loop or an LLM provider problem; CI's buffered output hides which."
tags: [playbook, ci, agent, mcp, debugging]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, test-agents job"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: mcp-stdio
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/mcp_stdio.py
    title: "_agent_base/src/agent_base/mcp_stdio.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: pin
    resource: https://github.com/telchak/daggerverse/commit/a61586f7128c367fa3d401232c3a2e09ae786d95
    title: "fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
---

# Symptom

`test-agents` matrix job fails at the 20-minute `timeout-minutes`, output empty: `ci.yml` buffers
`OUTPUT=$(dagger api call -m ./tests ... 2>&1)` and the buffer is discarded on timeout, even
though `DAGGER_PROGRESS: plain` streams the logs into it.[^ci]

# Likely causes

1. **A hung MCP session.** On v1.0.0-beta.21 `LLM.with_mcp_server` hangs on the second step of an
   LLM loop: the engine dials the server again and gets the running service without its stdin
   and stdout, so `initialize` is never answered. The agents therefore call MCP tools through
   `agent_base.mcp_stdio` (one exec per request, the server killed after 120 s); setting
   `ENGINE_MCP = True` brings the hang back.[^mcp-stdio] See the
   [MCP exec driver decision](/decisions/mcp-exec-driver.md).
2. **An MCP server that cannot start.** On 0.x the LLM then waited forever on a service that never
   answered: the cause of all 8 Daggie/Monty failures in August 2026 (`mcp` 2.0.0 removed
   `mcp.server.fastmcp`).[^pin] With the stdio driver the server is listed as `Unavailable: ...`
   in the system prompt's MCP catalog and its calls fail, so look for that line rather than a
   hang.[^mcp-stdio]
3. **An exploration loop.** See [exploration budget](/patterns/exploration-budget.md).
4. **LLM provider issue** (quota, model rename in `vars.GEMINI_MODEL`).

# Steps

1. Reproduce one test locally with live output:
   `DAGGER_PROGRESS=plain dagger api call -m ./tests daggie-explain` (needs `GEMINI_API_KEY`).
   The plain log, the TUI (without `DAGGER_PROGRESS`) or the Dagger Cloud trace
   (`DAGGER_CLOUD_TOKEN`) shows the step that hangs.
2. Run the MCP server's container alone, e.g. `dagger api call -m ./dagger-mcp container terminal`
   and start `python main.py`, or run its install in the same base image, to see the import error.
3. Pin or fix the dependency, and record why in code (`TEMPORARY PIN` comment) and in a
   [decision](/decisions/pin-mcp-below-2.md).

[^ci]: CI workflow, test-agents job
[^mcp-stdio]: _agent_base/src/agent_base/mcp_stdio.py
[^pin]: fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers
