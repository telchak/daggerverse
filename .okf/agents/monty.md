---
type: AI Agent
title: "Monty (Python agent)"
description: "AI Python development agent: assist, review, write tests, build/lint/typecheck and upgrade dependencies, with python-lft and pypi-query MCP servers."
resource: https://github.com/telchak/daggerverse/tree/main/monty
tags: [agent, llm, python]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/monty/src/monty/main.py
    title: "monty/src/monty/main.py"
    author: human:telchak
    last_modified: 2026-08-15T22:29:19+02:00
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/monty/README.md
    title: "monty/README.md"
    author: human:telchak
    last_modified: 2026-03-01T14:43:35+01:00
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/monty/src/monty/prompts
    title: "monty prompt files"
    author: human:telchak
    last_modified: 2026-02-21T18:58:15+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/monty/dagger.json
    title: "monty/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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
`suggest_github_fix`, `develop_github_issue`.[^main] Deterministic tools wrap
[python-build](/modules/python-build.md): `python_build`, `python_lint`, `python_test`,
`python_typecheck`, `python_install`.

Constructor: `source`, `python_version`, `self_improve`.

# MCP servers

| Name | Package | Notes |
|------|---------|-------|
| `python-lft` | `python-lft-mcp[tools]` from GitHub (not on PyPI) | ruff/black lint+format, pytest, mypy |
| `pypi` | `pypi-query-mcp-server` | versions, dependencies, download stats |

`python-lft-mcp` declares an unconstrained `mcp` dependency, so it broke at import with
`mcp` 2.0.0 exactly like [dagger-mcp](/modules/dagger-mcp.md); it is pinned `mcp<2`.
`pypi-query-mcp-server` constrains `fastmcp<3`, which held `mcp` at 1.29.0 and was
unaffected.[^pin] See the [decision](/decisions/pin-mcp-below-2.md).

Added 2026-02-11.[^added] Context files: `MONTY.md` + shared.

[^main]: monty/src/monty/main.py
[^added]: feat(monty): Add Monty agent
[^pin]: fix(daggie,monty): pin mcp<2 to unbreak Python MCP servers
