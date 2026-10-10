---
type: AI Agent
title: "Angie (Angular agent)"
description: "AI Angular development agent: assist, review, write tests, build and upgrade Angular projects, with the Angular CLI MCP server."
resource: https://github.com/telchak/daggerverse/tree/main/angie
tags: [agent, llm, angular]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-03-22T15:43:15+01:00
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/angie/README.md
    title: "angie/README.md"
    author: human:telchak
    last_modified: 2026-03-01T14:43:35+01:00
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/angie/src/angie/prompts
    title: "angie prompt files"
    author: human:telchak
    last_modified: 2026-02-21T18:58:15+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/angie/dagger.json
    title: "angie/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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
`review`), `suggest_github_fix`, `develop_github_issue`.[^main] Deterministic tools wrap the
[angular module](/modules/angular.md): `angular_build`, `angular_lint`, `angular_test`,
`angular_install`. Workspace tools and `task` come from [agent-base](/agents/agent-base.md).

Constructor: `source` (`DefaultPath("/")`), `node_version="22"`, `self_improve="off"`.

# Configuration specifics

- Context files: `("ANGIE.md", "AGENT.md", "CLAUDE.md")`.
- MCP: `ng mcp` from `@angular/cli` in a `node:<version>` container with an npm cache.
  Experimental tools are loaded per task (`_TASK_MCP_TOOLS`): `assist` gets
  `build,test,modernize`, `build` gets `build`, `upgrade` gets `modernize`, and `review`,
  `write_tests`, `suggest_fix` get no MCP server at all ("MCP can't see files and confuses the
  LLM").[^main] See [task-scoped MCP](/patterns/task-scoped-mcp.md).
- `write_tests` blocks the four `angular_*` tools so the LLM writes tests instead of running
  them, which could hang on missing browsers.[^mcp-opt]
- Router keys: `upgrade{target_version, dry_run}`, `build{command}`,
  `write_tests{target, test_framework}`.

# Tests

`.agent-tests` is absent, so CI runs the defaults: `assist review write-tests build upgrade`,
plus the dedicated `test-angie-github-issue` job that opens a real PR and closes it.
Angie tests still clone the Angular RealWorld example app.

First agent built on the workspace pattern (2026-02-10).[^added]

[^main]: angie/src/angie/main.py
[^added]: feat(angie): Add Angie Angular agent
[^mcp-opt]: fix: Block build/test tools during write_tests and optimize Angie MCP
