---
type: Known Issue
title: "Dagger 1.0 beta known issues"
description: "Problems hit while moving this repository to Dagger v1.0.0-beta.21, with causes and workarounds."
tags: [dagger, known-issue, gotcha, mcp, windows]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
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
  - id: mcp-stdio
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/mcp_stdio.py
    title: "_agent_base/src/agent_base/mcp_stdio.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: checks-go
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/checks.go
    title: "Dagger engine: generator staleness check (core/checks.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: session
    resource: local migration session on a Windows 11 host, 2026-10-24
    title: "Observations from the Dagger 1.0 migration session"
    author: claude-code/2.1.310
---

Observed with CLI and engine v1.0.0-beta.21 on 2026-10-24.[^session] Recheck each one when
bumping the engine and delete it once fixed.

| Issue | Cause | Workaround here |
|-------|-------|-----------------|
| An LLM with `LLM.with_mcp_server` hangs on its second step | `syncMCPSessions` stores sessions on a transient clone, so each step dials the server again; `startWithKey` finds the service already running under the same key and returns it without attaching the new stdio streams, so `initialize` is never answered[^mcp-go] [^services-go] | Agents list MCP tools in the system prompt and call them through an `mcp` tool that runs a one-shot stdio driver ([decision](/decisions/mcp-exec-driver.md)); `mcp_stdio.ENGINE_MCP = True` switches back[^mcp-stdio] |
| `dagger check` always fails the Python SDK staleness check on a Windows host | host files upload with mode 0755, generators write 0644, and the staleness check compares metadata: 1031 files "changed" with zero line changes[^checks-go] | none locally; trust `dagger generate --no-apply` showing no line changes, and the Linux CI `check` job |
| python-build's `check-lint` fails on a Windows host with ruff `EXE002` ("executable but no shebang") | the same 0755 upload modes | run it on Linux (CI) |
| A `Workspace` argument is empty when Dagger runs outside a Git repository with no `dagger.toml` (e.g. `dagger check -m <module>` in a bare folder) | nothing marks a workspace root there | run inside a Git repository or a directory with a `dagger.toml` |
| `dagger module migrate ./tests` on Windows: "Access is denied" renaming a temp file onto `dagger.toml` | file rename on Windows | `tests` was migrated by hand, then generated |
| A Python runtime module fails to load: uv "failed to rename file ... interpreter-v4 ... No such file or directory" | concurrent module loads sharing the uv cache volume | rerun |
| `dagger-for-github` with `verb: version` fails | it runs `dagger --progress plain version`; `version` and `api functions` reject `--progress` | install only (no `verb`), and set `DAGGER_PROGRESS=plain` for streaming logs, since non-TTY progress now defaults to a one-shot report[^ci] |
| `dag.current_node()` fails with "no current function call" in a module behind a static entrypoint | entrypoint code runs outside a function call | agents keep a runtime (`legacyRuntime = true`) |
| Unknown or snake_case names in `with_tools(..., except_=[...])` are ignored silently | the engine matches camelCase tool names | `llm_helpers.tool_exclusions` converts Python names |

Local tooling quirks of that session, not of Dagger: `dagger.exe` called from a non-console pipe
printed nothing (worked through `Start-Process` with redirected output), and a stored ghcr.io
credential got HTTP 403 (worked with an anonymous `DOCKER_CONFIG`).

Not verified: whether daggerverse.dev indexes modules that only have `dagger-module.toml`; see
[publishing](/dagger/daggerverse-publishing.md).

[^mcp-go]: Dagger engine: MCP sessions (core/mcp.go, syncMCPSessions)
[^services-go]: Dagger engine: service start and reuse (core/services.go, startWithKey)
[^mcp-stdio]: _agent_base/src/agent_base/mcp_stdio.py
[^checks-go]: Dagger engine: generator staleness check (core/checks.go)
[^ci]: CI workflow
[^session]: Observations from the Dagger 1.0 migration session
