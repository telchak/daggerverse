---
type: Decision
title: "Pin mcp<2 for Python MCP servers (temporary)"
description: "dagger-mcp and Monty's python-lft server install mcp<2 because mcp 2.0.0 removed mcp.server.fastmcp; remove once ported."
tags: [decision, mcp, dependencies, temporary]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: pin
    resource: https://github.com/telchak/daggerverse/commit/a61586f7128c367fa3d401232c3a2e09ae786d95
    title: "fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
---

# Context

`mcp` 2.0.0 (2026-07-28) removed `mcp.server.fastmcp`. Both Python MCP servers resolved it and
crashed at import, failing all 8 `test-agents` jobs for Daggie (3) and Monty (5). Angie (Node MCP),
Speck (no MCP) and Goose (Node gcloud MCP) passed.[^pin]

# Decision (2026-08-15)

Install `mcp<2` (resolves to 1.29.0) in [dagger-mcp](/modules/dagger-mcp.md) and next to
`python-lft-mcp` in [Monty](/agents/monty.md). Marked `TEMPORARY PIN` in code.

# Exit

Port `dagger-mcp/src/dagger_mcp/server/main.py` to the mcp 2.0 API, and drop Monty's pin once
`python-lft-mcp` supports mcp 2.0. Lesson: unpinned installs inside service containers break
silently; see [debug an agent CI timeout](/playbooks/debug-agent-ci-timeout.md).

[^pin]: fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers
