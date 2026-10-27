---
type: AI Agent
title: "Angie (Angular agent)"
description: "AI Angular development agent: assist, review, write tests, build and upgrade Angular projects, with the Angular CLI MCP server and an @agent function for dagger agent."
resource: https://github.com/telchak/daggerverse/tree/main/angie
tags: [agent, llm, angular]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/angie/README.md
    title: "angie/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/angie/src/angie/prompts
    title: "angie prompt files"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/angie/dagger-module.toml
    title: "angie/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/e28b97531869335ac0cd55a262b20fb6c60f40fd
    title: "feat(angie): Add Angie Angular agent"
    author: human:telchak
    last_modified: 2026-02-10T12:11:54+01:00
  - id: mcp-opt
    resource: https://github.com/telchak/daggerverse/commit/8e4e5025db4bc7f979c70911f4b50f6c7a9d5a33
    title: "fix: Block build/test tools during write_tests and optimize Angie MCP"
    author: human:telchak
    last_modified: 2026-02-21T19:26:19+01:00
---

# Entrypoints

`assist`, `review`, `write_tests`, `build`, `upgrade` (all return a `Directory` except
`review`), `suggest_github_fix`, `develop_github_issue`, and `agent` (`@agent`, for
`dagger agent`).[^main] Deterministic tools wrap the [angular module](/modules/angular.md):
`angular_build`, `angular_lint`, `angular_test`, `angular_install`, each taking the bound
`ws: dagger.Workspace`. Workspace tools, `mcp` and `task` come from
[agent-base](/agents/agent-base.md).

Constructor: `source` (`DefaultPath("/")`), `node_version="22"`, `self_improve="off"`; listed in
`_FIELDS` so they are not offered as tools. Runs on the Python SDK runtime
(`legacyRuntime`), with `_agent_base` included.[^manifest]

# Configuration specifics

- Context files: `("ANGIE.md", "AGENT.md", "CLAUDE.md")`.
- MCP: `ng mcp` from `@angular/cli` in a `node:<version>` container with an npm cache, called
  through the `mcp` tool. Experimental tools are loaded per task (`_TASK_MCP_TOOLS`): `assist`
  gets `build,test,modernize`, `build` gets `build`, `upgrade` gets `modernize`, and `review`,
  `write_tests`, `suggest_fix` get no MCP server at all ("MCP can't see files and confuses the
  LLM").[^main] See [task-scoped MCP](/patterns/task-scoped-mcp.md).
- `review` also blocks the destructive tools; `write_tests` blocks the four `angular_*` tools so
  the LLM writes tests instead of running them, which could hang on missing browsers.[^mcp-opt]
- Router keys: `upgrade{target_version, dry_run}`, `build{command}`,
  `write_tests{target, test_framework}`.

# Tests

`.agent-tests` is absent, so CI runs the defaults: `assist review write-tests build upgrade`,
plus the dedicated `test-angie-github-issue` job that opens a real PR and closes it.
Angie tests clone the Angular RealWorld example app. On 1.0, `assist` and `review` pass against
a scripted mock LLM (catalog of 9 Angular MCP tools, an `mcp` call, a `writeFile` edit).

First agent built on the workspace pattern (2026-02-10).[^added]

[^main]: angie/src/angie/main.py
[^manifest]: angie/dagger-module.toml
[^added]: feat(angie): Add Angie Angular agent
[^mcp-opt]: fix: Block build/test tools during write_tests and optimize Angie MCP
