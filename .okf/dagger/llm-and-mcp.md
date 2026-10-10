---
type: Reference
title: "Dagger LLM, Env and MCP"
description: "Dagger's native LLM type: environments with typed inputs/outputs, tool use over Dagger functions, blocked functions, and MCP in both directions."
tags: [dagger, llm, mcp, agents]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: llm
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/introduction/features/llm.mdx
    title: "Dagger docs: LLM Integration (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
  - id: agent-base
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/llm_helpers.py
    title: "agent_base/llm_helpers.py"
    author: human:telchak
    last_modified: 2026-02-28T16:53:12+01:00
  - id: goose-readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Goose section"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
---

# Model

`dag.llm()` runs an agent loop inside the engine. An `Env` declares inputs and outputs
(`with_string_input`, `with_container_input`, `with_workspace`, `with_string_output`...). The LLM
discovers Dagger functions on the objects in its env as tools, using their doc strings, and loops
until done; `env().output(name)` or `env().workspace()` read the results.[^llm]

As used in this repo:[^agent-base]

```python
llm = (
    dag.llm()
    .with_env(env.with_current_module())      # agent's own @functions become tools
    .with_system_prompt(system_prompt + context_md)
    .with_mcp_server("angular", service)      # MCP server as a Dagger Service
    .with_blocked_function("Angie", "assist") # prevent recursion
    .with_prompt_file(prompt_file)
)
result = await llm.env().workspace()
```

The provider is chosen from env vars (`GEMINI_API_KEY`/`GEMINI_MODEL`, `ANTHROPIC_*`, ...).

# MCP

- **Into Dagger:** `LLM.with_mcp_server(name, service)`. Only stdio MCP servers are supported, which
  is why Goose exposes the HTTP Developer Knowledge API as functions instead.[^goose-readme]
- **Out of Dagger:** `dagger -m <module> mcp` serves a module as an MCP server over stdio, for modules
  without required constructor args.[^llm]

Patterns built on this: [blocked functions](/patterns/blocked-functions.md),
[task-scoped MCP](/patterns/task-scoped-mcp.md), [output binding](/patterns/llm-output-binding.md).

[^llm]: Dagger docs: LLM Integration (v0.21.10)
[^agent-base]: agent_base/llm_helpers.py
[^goose-readme]: Repository README, Goose section
