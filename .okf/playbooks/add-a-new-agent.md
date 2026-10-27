---
type: Playbook
title: "Add a new AI agent"
description: "Steps to create a new coding agent on top of _agent_base on Dagger 1.0: runtime scope, clients, shared base, prompts, tests and CI wiring."
tags: [playbook, agent]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Creating a New Agent"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml, agent scopes"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/angie/dagger-module.toml
    title: "angie/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: pyproject
    resource: https://github.com/telchak/daggerverse/blob/main/angie/pyproject.toml
    title: "angie/pyproject.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

1. From the repository root, `dagger module init python --name <agent> --path <agent>`; this
   registers its scope in `dagger.toml`.[^readme]
2. Put it on the Python SDK runtime: `[sdks.python.scopes.<agent>.settings] legacyRuntime = true`
   in `dagger.toml`. Agents bind themselves to their LLM with `dag.current_node()`, which a
   generated static entrypoint cannot answer.[^workspace]
3. Clients: from `<agent>/`, `dagger module client add
   github.com/kpenfound/dag/github-issue@b316e472d3de5bb0e54fe3991be68dc85e33ef38 --sdk=python`,
   plus any deterministic module in the scope's `clients` (`./angular`).
4. Shared base: `include = ["../_agent_base"]` in `<agent>/dagger-module.toml`,[^manifest] and in
   `pyproject.toml` `"agent-base"` in `dependencies` with
   `agent-base = { path = "../_agent_base", editable = true }` in `[tool.uv.sources]`.[^pyproject]
5. `main.py` modelled on [Angie](/agents/angie.md):[^angie] `_CONTEXT_FILES`, `_CLASS_NAME`,
   `_ALLOWED_ROUTER_KEYS`, `_FIELDS` (constructor fields, hidden from the LLM),
   `_mcp_servers(task)` returning `agent_base.mcp_stdio.McpServer` entries plus an `mcp` tool (not
   `LLM.with_mcp_server`, see [MCP exec driver](/decisions/mcp-exec-driver.md)), `_load_prompt`,
   thin `@function` wrappers delegating to `agent_base`, file tools taking `ws: dagger.Workspace`,
   and an `@agent` function for `dagger agent`, as Angie, Monty and Daggie have. Block **only
   functions that exist** on the class, see [blocked functions](/patterns/blocked-functions.md).
6. Prompts in `src/<agent>/prompts/`: system, task_system, router, suggest_fix, one per entrypoint.
   They describe their inputs under `## Inputs`; the values are appended under `## Input values`.
   Include the efficiency budget, see [exploration budget](/patterns/exploration-budget.md). The
   `prompts/` directory is what makes CI treat it as an agent.[^ci]
7. `dagger generate -y`, then commit `dagger.toml`, `dagger.lock`, `sdk/`, `clients/` and
   `uv.lock`. The description is the docstring of `src/<agent>/__init__.py`.[^readme]
8. Tests: `Tests.<agent>_<suffix>` functions, `./<agent>` in the tests scope's `clients` (then
   `dagger generate -y`), and `.agent-tests` listing suffixes if they differ from
   `assist review write-tests build upgrade`; add `.agent-gcp` if it needs GCP credentials.
9. Add it to `sonar.cpd.exclusions`, README tables, and `.okf/agents/`.

[^readme]: Repository README, Creating a New Agent
[^workspace]: dagger.toml, agent scopes
[^manifest]: angie/dagger-module.toml
[^pyproject]: angie/pyproject.toml
[^angie]: angie/src/angie/main.py
[^ci]: CI workflow
