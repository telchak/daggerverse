---
type: Python Package
title: "_agent_base (shared agent library)"
description: "The shared Python package that holds workspace tools, LLM builders, GitHub integration and router logic for Angie, Monty, Daggie and Speck."
tags: [agent, shared-library, llm]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: constants
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/constants.py
    title: "agent_base/constants.py"
    author: human:telchak
    last_modified: 2026-02-26T14:32:33+01:00
  - id: llm
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/llm_helpers.py
    title: "agent_base/llm_helpers.py"
    author: human:telchak
    last_modified: 2026-02-28T16:53:12+01:00
  - id: gh
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/github_tools.py
    title: "agent_base/github_tools.py"
    author: human:telchak
    last_modified: 2026-02-22T02:17:19+01:00
  - id: routing
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/routing.py
    title: "agent_base/routing.py"
    author: human:telchak
    last_modified: 2026-02-21T18:58:15+01:00
  - id: ws
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/workspace.py
    title: "agent_base/workspace.py"
    author: human:telchak
    last_modified: 2026-02-17T11:52:47+01:00
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Shared Agent Base section"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
---

# What it is

`_agent_base/` is a plain Python package (`agent-base`, hatchling build, Python >= 3.13), not a
Dagger module: it has no `dagger.json`. Agents pull it in with `"include": ["../_agent_base"]` in
`dagger.json` and `agent-base = { path = "../_agent_base", editable = true }` under
`[tool.uv.sources]` in `pyproject.toml`.[^readme] Each agent's `main.py` stays a thin wrapper that
defines only its class name, constructor fields, MCP servers, prompt path, context file priority
and entrypoint signatures.

Used by [Angie](/agents/angie.md), [Monty](/agents/monty.md), [Daggie](/agents/daggie.md) and
[Speck](/agents/speck.md). [Goose](/agents/goose.md) predates it and keeps its own copies.

# Modules

| Module | Holds |
|--------|-------|
| `constants` | `BLOCKED_ENTRYPOINTS` (assist, review, write_tests, build, upgrade, develop_github_issue, suggest_github_fix), `BLOCKED_DESTRUCTIVE` (edit_file, write_file, suggest_github_pr_code_comment), `SELF_IMPROVE_MODES` (off, write, commit)[^constants] |
| `workspace` | pure `read_file` / `edit_file` / `write_file` / `glob` / `grep` implementations; edits return `(new_dir, Changeset)`[^ws] |
| `llm_helpers` | `build_llm`, `build_suggest_fix_llm`, `build_task_llm`, `read_context_file`, `commit_context_file`, `get_result_or_last_reply`[^llm] |
| `github_tools` | `suggest_github_fix_impl`, `suggest_github_pr_code_comment_impl`, `develop_github_issue_impl`[^gh] |
| `routing` | `parse_router_response`, `execute_routed_function`[^routing] |

# Key behaviours

- **Context files.** `read_context_file` reads up to three sections: the agent file
  (`ANGIE.md`, `MONTY.md`, ...), then the first of `AGENTS.md` > `AGENT.md` > `CLAUDE.md`, then
  extras such as `DAGGER.md`; each is truncated at 4000 characters.[^llm] See
  [context files and self-improvement](/patterns/context-files-and-self-improvement.md).
- **Output fallback.** `get_result_or_last_reply` reads the `result` output binding and falls
  back to `last_reply()` because Gemini sometimes answers in text without calling the binding.
  See [LLM output binding](/patterns/llm-output-binding.md).
- **Blocking.** Every LLM gets `with_blocked_function` for the entrypoints, and read-only
  sub-agents also block destructive tools. See [blocked functions](/patterns/blocked-functions.md).
- **Router.** Malformed router JSON falls back to `assist`; a routed call that leaves the
  workspace digest unchanged is retried once. See [develop-github-issue](/patterns/develop-github-issue.md).
- **grep** runs `grep -rn` in an `alpine` container with `expect=dagger.ExecExpect.ANY`, while the
  build modules use `dagger.ReturnType.ANY`; see [Python SDK conventions](/conventions/python-sdk.md).[^ws]

[^constants]: agent_base/constants.py
[^llm]: agent_base/llm_helpers.py
[^gh]: agent_base/github_tools.py
[^routing]: agent_base/routing.py
[^ws]: agent_base/workspace.py
[^readme]: Repository README, Shared Agent Base section
