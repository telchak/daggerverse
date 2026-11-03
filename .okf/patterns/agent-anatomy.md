---
type: Design Pattern
title: "Agent anatomy"
description: "The common shape of every daggerverse AI agent in Dagger 1.0: a Dagger object on the Python SDK runtime with LLM entrypoints, workspace tools, an mcp tool, prompts, an optional @agent function and GitHub integration."
tags: [agent, llm, pattern]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, AI Agents and Creating a New Agent"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace-toml
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml, agent scopes"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, discover job"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace-pattern
    resource: https://github.com/telchak/daggerverse/commit/2a4542569eed90a6be6b0a8e552a0ca868b1c492
    title: "refactor(angie): use workspace pattern and return Directory for code-generating functions"
    author: human:telchak
    last_modified: 2026-02-10T18:50:52+01:00
---

# Shape

An agent is a Dagger module whose main class:[^angie]

1. Holds a `source: Directory` constructor field (`DefaultPath("/")`) plus agent settings and
   `self_improve`, all listed in `_FIELDS` so they are not offered as tools.
2. Exposes **entrypoints** (`assist`, `review`, `write_tests`, `build`, `upgrade`, ...). Each
   builds an LLM bound to `source.as_workspace()` and to the agent object itself
   (`with_tools(dag.current_node(), except_=...)`), with a system prompt, the task prompt plus its
   input values, and an MCP catalog, then returns the edited workspace as a `Directory` or the
   final reply as a string. See [LLM and MCP](/dagger/llm-and-mcp.md).
3. Exposes **tools** the LLM calls: workspace tools (`read_file`, `edit_file`, `write_file`,
   `glob`, `grep`, taking the bound `ws: dagger.Workspace`), deterministic build tools, `mcp`, and
   `task` (a read-only sub-agent on the same workspace).
4. Optionally exposes an `@agent` function (Angie, Monty, Daggie) that folds its tools and system
   prompt onto the base LLM of `dagger agent`.
5. Loads prompts from `src/<agent>/prompts/*.md` via `dag.current_module().source().file(...)`.

Code-generating entrypoints return the modified workspace `Directory` rather than text, so the
caller can export it or open a PR from it.[^workspace-pattern]

Agents run on the Python SDK runtime (`legacyRuntime = true` in their `dagger.toml` scope):
`dag.current_node()` needs a running function call, which code behind a static entrypoint does not
have, and `include` (for `_agent_base`) is only valid on a runtime manifest.[^workspace-toml]

# Prompt files

`system_prompt.md`, `task_system_prompt.md`, one `<entrypoint>_prompt.md` per entrypoint,
`router_prompt.md` and `suggest_fix_prompt.md`. Tool names in prompts are camelCase (`readFile`).
CI classifies a module as an agent purely because `src/*/prompts/` exists.[^ci]

# Cross-cutting behaviours

- [Context files and self-improvement](/patterns/context-files-and-self-improvement.md)
- [Blocked functions](/patterns/blocked-functions.md)
- [Task-scoped MCP servers](/patterns/task-scoped-mcp.md)
- [LLM results and fallbacks](/patterns/llm-output-binding.md)
- [Exploration budget](/patterns/exploration-budget.md)
- [develop-github-issue](/patterns/develop-github-issue.md)
- [suggest-github-fix](/patterns/suggest-github-fix.md)

Building a new one: [add a new agent](/playbooks/add-a-new-agent.md).[^readme]

[^readme]: Repository README, AI Agents and Creating a New Agent
[^angie]: angie/src/angie/main.py
[^workspace-toml]: dagger.toml, agent scopes
[^ci]: CI workflow, discover job
[^workspace-pattern]: refactor(angie): use workspace pattern and return Directory for code-generating functions
