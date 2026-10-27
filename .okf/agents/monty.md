---
type: AI Agent
title: "Monty (Python agent)"
description: "AI Python development agent: assist, review, write tests, build/lint/typecheck and upgrade dependencies, with python-lft and pypi-query MCP servers and an @agent function."
resource: https://github.com/telchak/daggerverse/tree/main/monty
tags: [agent, llm, python]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/monty/src/monty/main.py
    title: "monty/src/monty/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/monty/README.md
    title: "monty/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/monty/src/monty/prompts
    title: "monty prompt files"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/monty/dagger-module.toml
    title: "monty/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/f19c6ddc1006b47e36381696309e2cf036a84fa0
    title: "feat(monty): Add Monty agent"
    author: human:telchak
    last_modified: 2026-02-11T20:58:22+01:00
  - id: pin
    resource: https://github.com/telchak/daggerverse/commit/a61586f7128c367fa3d401232c3a2e09ae786d95
    title: "fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
---

# Entrypoints

`assist`, `review`, `write_tests`, `build`, `upgrade(target_package, target_version)`,
`suggest_github_fix`, `develop_github_issue`, and `agent` (`@agent`).[^main] Deterministic
tools wrap [python-build](/modules/python-build.md): `python_build`, `python_lint`,
`python_test`, `python_typecheck`, `python_install`, each taking the bound `ws`. `review` blocks
the destructive tools; `write_tests` blocks the five `python_*` tools.

Constructor: `source`, `python_version`, `self_improve` (in `_FIELDS`). Runs on the Python SDK
runtime with `_agent_base` included.[^manifest]

# MCP servers

Both are called through the `mcp` tool ([task-scoped MCP](/patterns/task-scoped-mcp.md)):

| Name | Package | Notes |
|------|---------|-------|
| `python-lft` | `python-lft-mcp[tools]` from GitHub (not on PyPI), command `python -m python_lft` | ruff/black lint+format, pytest, mypy |
| `pypi` | `pypi-query-mcp-server` | versions, dependencies, download stats; `live=True`, so answers are never cached |

`python-lft-mcp` declares an unconstrained `mcp` dependency, so it broke at import with
`mcp` 2.0.0 exactly like [dagger-mcp](/modules/dagger-mcp.md); it is pinned `mcp<2`.
`pypi-query-mcp-server` constrains `fastmcp<3`, which held `mcp` at 1.29.0 and was
unaffected.[^pin] See the [decision](/decisions/pin-mcp-below-2.md).

Added 2026-02-11.[^added] Context files: `MONTY.md` + shared. On 1.0, `assist` passes against a
scripted mock LLM.

[^main]: monty/src/monty/main.py
[^manifest]: monty/dagger-module.toml
[^added]: feat(monty): Add Monty agent
[^pin]: fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers
