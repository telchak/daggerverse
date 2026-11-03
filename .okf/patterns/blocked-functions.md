---
type: Design Pattern
title: "Blocked functions"
description: "Which of an agent's own functions and fields are excluded from its LLM tool set (with_tools except_), why the names must be camelCase, and the rule that only functions that exist may be listed."
tags: [agent, llm, pattern, gotcha]
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
    title: "agent_base/llm_helpers.py (tool_name, tool_exclusions)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: design
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/hack/designs/workspace-agents.md
    title: "Dagger design: Workspace Agents, object tools (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: daggie-fix
    resource: https://github.com/telchak/daggerverse/commit/6c940b919615dc3e0efbe4211c3adccb8372dce6
    title: "fix(daggie): block only existing entrypoints to prevent LLM hallucination"
    author: human:telchak
    last_modified: 2026-02-24T12:21:56+01:00
  - id: sub
    resource: https://github.com/telchak/daggerverse/commit/04fa7185ed302bd97a395f6e80abe9a65b05a3c6
    title: "fix: Block sub-agents tools"
    author: human:telchak
    last_modified: 2026-02-22T18:11:52+01:00
---

# Why

An agent binds itself to its LLM with `with_tools(dag.current_node(), except_=[...])`: every
eligible method becomes a tool, and so does every exposed field.[^design] Without exclusions an
agent's LLM could call its own entrypoints (`assist` calling `assist`) and recurse, a read-only
task could edit files, and field getters (`source`, `nodeVersion`) would clutter the tool set.
`@agent` functions are excluded automatically.[^design]

# Rules

- Every LLM excludes the agent's entrypoints (`BLOCKED_ENTRYPOINTS`) and its constructor fields
  (`_FIELDS`).[^constants]
- Read-only LLMs (`review`, Daggie's `explain`, the `task` sub-agent, `suggest_github_fix`) also
  exclude `BLOCKED_DESTRUCTIVE` (`edit_file`, `write_file`; Goose adds its deploy, delete and
  publish tools).[^sub] `suggest_github_fix` replies with JSON and the code posts the comments,
  so it needs no output tool.
- An LLM with no MCP server excludes the `mcp` tool; `write_tests` excludes the build/test tools
  so the model writes tests instead of running them.
- **Names are GraphQL names.** `except_` compares camelCase tool names and silently ignores names
  it does not know, so `"write_file"` would hide nothing. Lists hold Python names and go through
  `llm_helpers.tool_exclusions`, which converts them.[^llm]
- **Only list functions that exist on the class.** In 0.x, blocking a missing function raised
  `function "X" not found on type "Y"`, and listing absent functions made the LLM aware of them
  and hallucinate calls.[^daggie-fix] In 1.0 a missing name is ignored without a word, which hides
  typos. Daggie, Speck and Goose keep their own entrypoint lists for this reason.

[^constants]: agent_base/constants.py
[^llm]: agent_base/llm_helpers.py (tool_name, tool_exclusions)
[^design]: Dagger design: Workspace Agents, object tools (v1.0.0-beta.21)
[^daggie-fix]: fix(daggie): block only existing entrypoints to prevent LLM hallucination
[^sub]: fix: Block sub-agents tools
