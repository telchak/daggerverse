---
type: Playbook
title: "Add a new AI agent"
description: "Steps to create a new coding agent on top of _agent_base, with prompts, tests and CI wiring."
tags: [playbook, agent]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Creating a New Agent"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-03-22T15:43:15+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
---

1. `dagger init <agent> --sdk python`.[^readme]
2. `dagger.json`: `description`, `"include": ["../_agent_base"]`, `github-issue` dependency pinned
   to `b316e472d3de5bb0e54fe3991be68dc85e33ef38`, plus any deterministic module (`../angular`).
3. `pyproject.toml`: `dependencies = ["dagger-io", "agent-base"]` and
   `agent-base = { path = "../_agent_base", editable = true }` in `[tool.uv.sources]`; commit `uv.lock`.
4. `main.py` modelled on [Angie](/agents/angie.md):[^angie] `_CONTEXT_FILES`, `_CLASS_NAME`,
   `_ALLOWED_ROUTER_KEYS`, `_mcp_servers(task)`, `_load_prompt`, thin `@function` wrappers delegating
   to `agent_base`. Block **only functions that exist** on the class, see
   [blocked functions](/patterns/blocked-functions.md).
5. Prompts in `src/<agent>/prompts/`: system, task_system, router, suggest_fix, one per entrypoint.
   Include the efficiency budget, see [exploration budget](/patterns/exploration-budget.md). The
   `prompts/` directory is what makes CI treat it as an agent.[^ci]
6. `dagger develop`, then re-add `description` to `dagger.json` (it gets stripped).
7. Tests: `Tests.<agent>_<suffix>` functions, and `.agent-tests` listing suffixes if they differ
   from `assist review write-tests build upgrade`; add `.agent-gcp` if it needs GCP credentials.
8. Add it to `sonar.cpd.exclusions`, README tables, and `.okf/agents/`.

[^readme]: Repository README, Creating a New Agent
[^angie]: angie/src/angie/main.py
[^ci]: CI workflow
