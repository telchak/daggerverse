---
type: Design Pattern
title: "Exploration budget in prompts"
description: "System prompts cap agents at about 15 tool calls and forbid reading every file, to stop CI exploration spirals and timeouts."
tags: [agent, llm, pattern, ci]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: spirals
    resource: https://github.com/telchak/daggerverse/commit/a14d74346cf311327a35a0369f0a6982908b3f94
    title: "fix: prevent agent exploration spirals in CI"
    author: human:telchak
    last_modified: 2026-02-12T00:09:44+01:00
  - id: timeout
    resource: https://github.com/telchak/daggerverse/commit/a2425cbc60970e211786cc43b94a18278980d94e
    title: "fix(ci): add 20min timeout to agent tests and tighten build prompt"
    author: human:telchak
    last_modified: 2026-02-12T22:21:44+01:00
  - id: angie-system
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/prompts/system_prompt.md
    title: "Angie system prompt"
    author: human:telchak
    last_modified: 2026-02-21T17:12:34+01:00
---

Every agent system prompt carries an `## Efficiency` section:[^angie-system]

- Do NOT read every file. `glob` the layout, read only key files.
- Use MCP tools sparingly.
- Aim for under 15 tool calls; after 10, wrap up.
- Never loop.

It was added on 2026-02-12 after agents wandered through whole repositories in CI,[^spirals]
together with a 20-minute `timeout-minutes` on each agent test step.[^timeout] A hung MCP server
also surfaces as that 20-minute timeout; see
[debug an agent CI timeout](/playbooks/debug-agent-ci-timeout.md).

[^spirals]: fix: prevent agent exploration spirals in CI
[^timeout]: fix(ci): add 20min timeout to agent tests and tighten build prompt
[^angie-system]: Angie system prompt
