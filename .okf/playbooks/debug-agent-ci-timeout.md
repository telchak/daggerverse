---
type: Playbook
title: "Debug an agent test that times out in CI"
description: "An agent CI job that dies at exactly 20 minutes with no traceback usually means an MCP service never started or the agent looped."
tags: [playbook, ci, agent, mcp, debugging]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: pin
    resource: https://github.com/telchak/daggerverse/commit/a61586f7128c367fa3d401232c3a2e09ae786d95
    title: "fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, test-agents job"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
---

# Symptom

`test-agents` matrix job fails at the 20-minute `timeout-minutes`, output empty: `ci.yml` buffers
`OUTPUT=$(dagger call ... 2>&1)` and the buffer is discarded on timeout.[^ci]

# Likely causes

1. **An MCP server container crashed at startup.** The LLM waits forever on a service that never
   answers. This was the cause of all 8 Daggie/Monty failures in August 2026 (`mcp` 2.0.0 removed
   `mcp.server.fastmcp`).[^pin] Look at which agents fail: if only Python-MCP agents fail, suspect
   this.
2. **An exploration loop.** See [exploration budget](/patterns/exploration-budget.md).
3. **LLM provider issue** (quota, model rename in `vars.GEMINI_MODEL`).

# Steps

1. Reproduce one test locally with live output: `dagger call -m tests daggie-explain` (needs
   `GEMINI_API_KEY`). The TUI or Dagger Cloud trace (`DAGGER_CLOUD_TOKEN`) shows the hung service.
2. Start the MCP service alone, e.g. `dagger -m dagger-mcp call server up`, or run its install in
   the same base image to see the import error.
3. Pin or fix the dependency, and record why in code (`TEMPORARY PIN` comment) and in a
   [decision](/decisions/pin-mcp-below-2.md).

[^pin]: fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers
[^ci]: CI workflow, test-agents job
