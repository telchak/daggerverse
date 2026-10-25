---
type: Reference
title: "Dagger LLM, workspace agents and MCP"
description: "Dagger 1.0's LLM type: a workspace binding, object tools, built-in trace and skill tools, @agent functions, provider configuration, and MCP in both directions."
tags: [dagger, llm, mcp, agents]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: design
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/hack/designs/workspace-agents.md
    title: "Dagger design: Workspace Agents (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: llm-type
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/partials/types/_llm.mdx
    title: "Dagger docs: LLM type (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: mcp-go
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/mcp.go
    title: "Dagger engine: LLM tool set and built-in tools (core/mcp.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: skills-go
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/llm_skills.go
    title: "Dagger engine: LLM skills (core/llm_skills.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: mcp-cmd
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/internal/cmd/dagger/mcp.go
    title: "Dagger CLI: dagger mcp (hidden, experimental)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: agent-base
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/llm_helpers.py
    title: "agent_base/llm_helpers.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: session
    resource: local migration session on a Windows 11 host, 2026-10-24
    title: "Observations from the Dagger 1.0 migration session (scripted mock LLM)"
    author: claude-code/2.1.310
---

# Model

`Env` is gone in 1.0. An LLM starts unbound and is given:[^design] [^llm-type]

- a **workspace** (`with_workspace`; a Directory becomes one with `as_workspace()`): its mutable
  state. Edits stage in an overlay; nothing reaches the host unless exported.
- **object tools** (`with_tools(obj, except_=[...])`): every eligible method of the object becomes
  a tool named after it (camelCase), described by its docstring, with its scalar arguments;
  `Workspace` arguments are injected from the bound workspace and hidden. `dag.current_node()`
  binds the object whose function is running, which only works inside a function call.
- results by return type: a `Changeset` or `Workspace` updates the bound workspace, the object's
  own type rebinds it as the new state, scalars are returned, other objects are synced.

`loop()` runs the conversation; `last_reply()` and `workspace()` read it but do not run it.
Identical LLM chains are cached like any other call.[^session]

Built-in tools are always added: trace inspection (`ReadTrace`, `FindSpans`, `ReadLogs`,
`InspectCall`, `FindCalls`, `ListServices`, and `LoadTrace`, which imports a Dagger Cloud trace by
ID or URL), `FindArtifacts`, `Timeout`, and skills.[^mcp-go] Skills (`ListSkills`, `ReadSkill`)
come from the engine's own Dang skills, directories added with `with_skills(dir)`, and every
`SKILL.md` in the bound workspace.[^skills-go]

# @agent functions

An `@agent` function is middleware, `agent(base: LLM, ws: Workspace) -> LLM`. `dagger agent`
composes every installed agent module into one interactive prompt; `@agent` methods are left out
of `with_tools` automatically.[^design]

# Providers

Configured from env vars: `GEMINI_API_KEY` / `GEMINI_MODEL` (provider `google`, used by CI),
`ANTHROPIC_*`, `OPENAI_*`, or an OpenAI-compatible endpoint with `LOCAL_BASE_URL`, `LOCAL_MODEL`,
`LOCAL_API_COMPAT=openai`, `LOCAL_API_KEY` (reached through the client, so `127.0.0.1` works).
Remote modules need `--allow-llm` or `DAGGER_ALLOW_LLM`. `llm.tools()` lists the tool set
without calling a model.[^session]

# As used in this repo

```python
llm = (
    dag.llm()
    .with_workspace(source.as_workspace())
    .with_tools(dag.current_node(), except_=tool_exclusions([*blocked, *mcp_stdio.blocked_tools(servers)]))
)
llm, mcp_context = await mcp_stdio.attach(llm, servers)        # MCP catalog for the `mcp` tool
llm = llm.with_system_prompt(system_prompt + context_md + mcp_context)
result = await llm.with_prompt(prompt + format_inputs(inputs)).loop().last_reply()
```

`tool_exclusions` converts Python names to camelCase, because unknown names are ignored silently.[^agent-base]
See [agent-base](/agents/agent-base.md), [blocked functions](/patterns/blocked-functions.md),
[output binding](/patterns/llm-output-binding.md) and [task-scoped MCP](/patterns/task-scoped-mcp.md).

# MCP

- **Into Dagger:** `LLM.with_mcp_server(name, service)` (stdio servers). In v1.0.0-beta.21 it
  hangs on the second step, so the agents use their own driver: see
  [known issues](/dagger/known-issues-1-0-beta.md) and the [decision](/decisions/mcp-exec-driver.md).
- **Out of Dagger:** `dagger -m <module> mcp` serves a module as a stdio MCP server; in 1.0 the
  command is hidden and marked experimental.[^mcp-cmd]

[^design]: Dagger design: Workspace Agents (v1.0.0-beta.21)
[^llm-type]: Dagger docs: LLM type (v1.0.0-beta.21)
[^mcp-go]: Dagger engine: LLM tool set and built-in tools (core/mcp.go)
[^skills-go]: Dagger engine: LLM skills (core/llm_skills.go)
[^mcp-cmd]: Dagger CLI: dagger mcp (hidden, experimental)
[^agent-base]: agent_base/llm_helpers.py
[^session]: Observations from the Dagger 1.0 migration session (scripted mock LLM)
