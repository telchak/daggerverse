---
type: Python Package
title: "_agent_base (shared agent library)"
description: "The shared Python package that holds workspace tools, LLM builders, the MCP stdio driver, GitHub integration and router logic for all five agents."
tags: [agent, shared-library, llm, mcp]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: constants
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/constants.py
    title: "agent_base/constants.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: llm
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/llm_helpers.py
    title: "agent_base/llm_helpers.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: mcp
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/mcp_stdio.py
    title: "agent_base/mcp_stdio.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: gh
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/github_tools.py
    title: "agent_base/github_tools.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: routing
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/routing.py
    title: "agent_base/routing.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ws
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/workspace.py
    title: "agent_base/workspace.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/angie/dagger-module.toml
    title: "angie/dagger-module.toml (an agent's runtime manifest)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# What it is

`_agent_base/` is a plain Python package (`agent-base`, hatchling build, Python >= 3.13), not a
Dagger module. Each agent ships it with `include = ["../_agent_base"]` in its runtime
`dagger-module.toml` and installs it with `agent-base = { path = "../_agent_base", editable = true }`
under `[tool.uv.sources]`.[^manifest] An agent's `main.py` stays a thin wrapper: class name,
constructor fields (`_FIELDS`), MCP servers, prompt path, context files and entrypoints.

Used by all five agents: [Angie](/agents/angie.md), [Monty](/agents/monty.md),
[Daggie](/agents/daggie.md), [Speck](/agents/speck.md) and, since the 1.0 port,
[Goose](/agents/goose.md).

# Modules

| Module | Holds |
|--------|-------|
| `constants` | `BLOCKED_ENTRYPOINTS` (assist, review, write_tests, build, upgrade, develop_github_issue, suggest_github_fix), `BLOCKED_DESTRUCTIVE` (edit_file, write_file), `SELF_IMPROVE_MODES` (off, write, commit); Python names[^constants] |
| `workspace` | `read_file` / `edit_file` / `write_file` / `glob` / `grep` on a `dagger.Workspace`; edits return the new Workspace, which rebinds the LLM's workspace[^ws] |
| `llm_helpers` | `build_llm`, `build_suggest_fix_llm`, `build_task_llm`, `build_agent` (for `@agent`), `reply`, `edited_directory`, `tool_name` / `tool_exclusions`, `format_inputs`, `read_context_file`, `commit_context_file`[^llm] |
| `mcp_stdio` | `McpServer`, the MCP catalog for the system prompt, `call` (one-shot stdio driver), `attach`, `blocked_tools`, `ENGINE_MCP`[^mcp] |
| `github_tools` | `suggest_github_fix_impl` (JSON reply, code posts at most 5 comments), `parse_suggestions`, `truncate_error_output` (last 8000 chars), `develop_github_issue_impl`[^gh] |
| `routing` | `extract_json_object`, `parse_router_reply`, `execute_routed_function`[^routing] |

# Key behaviours

- **Binding.** `build_llm` binds `source.as_workspace()` and the agent object
  (`with_tools(dag.current_node(), except_=...)`); inputs go into the prompt under
  `## Input values`; `reply` / `edited_directory` run the loop.[^llm] See
  [LLM and MCP](/dagger/llm-and-mcp.md) and [output binding](/patterns/llm-output-binding.md).
- **Blocking.** Names are Python names, converted to camelCase by `tool_exclusions`; read-only
  tasks also block the destructive tools, and the `mcp` tool is hidden when a task has no MCP
  server. See [blocked functions](/patterns/blocked-functions.md).
- **MCP.** Servers are listed in the system prompt and called through the agent's `mcp` tool,
  because `LLM.with_mcp_server` hangs in v1.0.0-beta.21. See
  [task-scoped MCP](/patterns/task-scoped-mcp.md) and the [decision](/decisions/mcp-exec-driver.md).
- **Context files.** `read_context_file` reads up to three sections: the agent file
  (`ANGIE.md`, `MONTY.md`, ...), then the first of `AGENTS.md` > `AGENT.md` > `CLAUDE.md`, then
  extras such as `DAGGER.md`; each is truncated at 4000 characters.[^llm] See
  [context files and self-improvement](/patterns/context-files-and-self-improvement.md).
- **Router.** The router replies with JSON (bare, fenced or embedded); malformed replies fall back
  to `assist`; a routed call that leaves the workspace digest unchanged is retried once with a
  note. See [develop-github-issue](/patterns/develop-github-issue.md).
- **grep** runs `grep -rn` in an `alpine` container with `expect=dagger.ReturnType.ANY`.[^ws]

[^constants]: agent_base/constants.py
[^llm]: agent_base/llm_helpers.py
[^mcp]: agent_base/mcp_stdio.py
[^gh]: agent_base/github_tools.py
[^routing]: agent_base/routing.py
[^ws]: agent_base/workspace.py
[^manifest]: angie/dagger-module.toml (an agent's runtime manifest)
