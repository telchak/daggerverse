---
type: Design Pattern
title: "Task-scoped MCP servers"
description: "Agents attach MCP servers (and experimental MCP tools) only to the entrypoints that benefit, to save startup time and avoid confusing the model."
tags: [agent, mcp, pattern]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-03-22T15:43:15+01:00
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/main.py
    title: "daggie/src/daggie/main.py"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
  - id: goose
    resource: https://github.com/telchak/daggerverse/blob/main/goose/src/goose/main.py
    title: "goose/src/goose/main.py"
    author: human:telchak
    last_modified: 2026-02-28T16:53:12+01:00
  - id: perf
    resource: https://github.com/telchak/daggerverse/commit/1f77e994938ca92059721a5a895454e3f8da3f36
    title: "feat: Improve CI caching, agent reliability, and MCP startup performance"
    author: human:telchak
    last_modified: 2026-02-21T18:58:15+01:00
---

# Per agent

| Agent | Table | MCP on | MCP off |
|-------|-------|--------|---------|
| Angie | `_TASK_MCP_TOOLS` (experimental `ng mcp` tools per task) | assist (build,test,modernize), build (build), upgrade (modernize) | review, write_tests, suggest_fix[^angie] |
| Daggie | `_TASK_MCP_TOOLS` | assist, explain, debug | review[^daggie] |
| Goose | `_TASK_NEEDS_MCP` | assist, troubleshoot, upgrade | deploy, review[^goose] |
| Monty | none | both servers on every task | |
| Speck | none | | always (no MCP) |

Rationale recorded in Angie's code: for review "MCP can't see files and confuses the LLM", and
write_tests "just needs to read code and write test files". MCP servers are containers that
must install and start before the LLM's first turn, so skipping them also cuts startup time.[^perf]

MCP servers are passed as Dagger `Service`s through `llm.with_mcp_server(name, service)`; Dagger
only supports stdio MCP servers. See [Dagger LLM and MCP](/dagger/llm-and-mcp.md).

[^angie]: angie/src/angie/main.py
[^daggie]: daggie/src/daggie/main.py
[^goose]: goose/src/goose/main.py
[^perf]: feat: Improve CI caching, agent reliability, and MCP startup performance
