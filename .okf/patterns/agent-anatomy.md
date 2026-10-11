---
type: Design Pattern
title: "Agent anatomy"
description: "The common shape of every daggerverse AI agent: a Dagger object with LLM entrypoints, workspace tools, prompts, MCP services and GitHub integration."
tags: [agent, llm, pattern]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, AI Agents and Creating a New Agent"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-03-22T15:43:15+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, discover job"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
  - id: workspace-pattern
    resource: https://github.com/telchak/daggerverse/commit/2a4542569eed90a6be6b0a8e552a0ca868b1c492
    title: "refactor(angie): use workspace pattern and return Directory for code-generating functions"
    author: human:telchak
    last_modified: 2026-02-10T18:50:52+01:00
---

# Shape

An agent is a Dagger module whose main class:[^angie]

1. Holds a `source: Directory` constructor field (`DefaultPath("/")`) plus agent settings and
   `self_improve`.
2. Exposes **entrypoints** (`assist`, `review`, `write_tests`, `build`, `upgrade`, ...). Each
   builds a `dag.env()` with the workspace and string inputs, attaches a system prompt + task
   prompt, MCP servers and blocked functions, then returns `env().workspace()` (a `Directory`) or
   a `result` string output.
3. Exposes **tools** the LLM calls: workspace tools (`read_file`, `edit_file`, `write_file`,
   `glob`, `grep`), deterministic build tools, and `task` (a read-only sub-agent).
4. Loads prompts from `src/<agent>/prompts/*.md` via `dag.current_module().source().file(...)`.

Code-generating entrypoints return the modified workspace `Directory` rather than text, so the
caller can `export` it or open a PR from it.[^workspace-pattern]

# Prompt files

`system_prompt.md`, `task_system_prompt.md`, one `<entrypoint>_prompt.md` per entrypoint,
`router_prompt.md` and `suggest_fix_prompt.md`. CI classifies a module as an agent purely
because `src/*/prompts/` exists.[^ci]

# Cross-cutting behaviours

- [Context files and self-improvement](/patterns/context-files-and-self-improvement.md)
- [Blocked functions](/patterns/blocked-functions.md)
- [Task-scoped MCP servers](/patterns/task-scoped-mcp.md)
- [LLM output binding](/patterns/llm-output-binding.md)
- [Exploration budget](/patterns/exploration-budget.md)
- [develop-github-issue](/patterns/develop-github-issue.md)
- [suggest-github-fix](/patterns/suggest-github-fix.md)

Building a new one: [add a new agent](/playbooks/add-a-new-agent.md).[^readme]

[^readme]: Repository README, AI Agents and Creating a New Agent
[^angie]: angie/src/angie/main.py
[^ci]: CI workflow, discover job
[^workspace-pattern]: refactor(angie): use workspace pattern and return Directory for code-generating functions
