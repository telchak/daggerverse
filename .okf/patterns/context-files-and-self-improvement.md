---
type: Design Pattern
title: "Context files and self-improvement"
description: "How agents read per-repo context (AGENT-specific file + AGENTS.md) and, with --self-improve, write learned context back."
tags: [agent, context-engineering, pattern]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: llm
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/llm_helpers.py
    title: "agent_base/llm_helpers.py"
    author: human:telchak
    last_modified: 2026-02-28T16:53:12+01:00
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Self-Improvement section"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/18ce6499eba2f246708c63786265f9c87cd4337c
    title: "feat: Add self-improvement option to agents"
    author: human:telchak
    last_modified: 2026-02-26T14:32:33+01:00
  - id: split
    resource: https://github.com/telchak/daggerverse/commit/29a87988b78ca0ca8ba5f35100b944bb44c990dc
    title: "feat(agents): split context file reads and writes into agent-specific and shared files"
    author: human:telchak
    last_modified: 2026-02-28T16:35:58+01:00
---

# Reading

Before every LLM call the agent reads, from the root of the `source` directory:[^llm]

1. its own file (`ANGIE.md`, `MONTY.md`, `DAGGIE.md`, `GOOSE.md`, `SPECK.md`),
2. the first match of `AGENTS.md` > `AGENT.md` > `CLAUDE.md` (shared),
3. extra files (`DAGGER.md` for Daggie and Goose).

Each section is truncated at 4000 characters ("~1000 tokens") and appended to the system prompt
as `## Project Context (from <file>)`.

**Consequence for this repo:** when an agent runs against this repository with no `AGENTS.md`,
it reads the root `CLAUDE.md`, and only the first 4000 characters of it. Keep the top of
`CLAUDE.md` self-sufficient.

# Writing (`--self-improve`)

| Mode | Behaviour |
|------|-----------|
| `off` (default) | nothing |
| `write` | the agent appends learnings under `## Learned Context` in its own file and in `AGENTS.md` |
| `commit` | same, then `commit_context_file` commits both in an `alpine/git` container as `chore(<agent>): update context files with learned discoveries` |

Agent-specific knowledge (framework patterns, tool gotchas) goes in the agent file; repository
knowledge (architecture, CI, conventions) goes in `AGENTS.md`.[^readme] Introduced 2026-02-26[^added]
and split into two files on 2026-02-28.[^split] Applies to directory-returning entrypoints.

This is the same idea as this OKF bundle, at a smaller scale; see the root `CLAUDE.md`.

[^llm]: agent_base/llm_helpers.py
[^readme]: Repository README, Self-Improvement section
[^added]: feat: Add self-improvement option to agents
[^split]: feat(agents): split context file reads and writes into agent-specific and shared files
