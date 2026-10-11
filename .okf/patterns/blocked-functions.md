---
type: Design Pattern
title: "Blocked functions"
description: "Why and how agents call with_blocked_function, and the rule that only functions that exist on the class may be blocked."
tags: [agent, llm, pattern, gotcha]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: constants
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/constants.py
    title: "agent_base/constants.py"
    author: human:telchak
    last_modified: 2026-02-26T14:32:33+01:00
  - id: daggie-fix
    resource: https://github.com/telchak/daggerverse/commit/6c940b919615dc3e0efbe4211c3adccb8372dce6
    title: "fix(daggie): block only existing entrypoints to prevent LLM hallucination"
    author: human:telchak
    last_modified: 2026-02-24T12:21:56+01:00
  - id: sub
    resource: https://github.com/telchak/daggerverse/commit/04fa7185ed302bd97a395f6e80abe9a65b05a3c6
    title: "fix: Block sub-agents tools"
    author: human:telchak
    last_modified: 2026-02-22T18:11:52+01:00
  - id: system
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, Blocked Functions"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
---

# Why

The Dagger LLM sees every function of the current module as a tool (`env.with_current_module()`).
Without blocking, an agent's LLM could call its own entrypoints (`assist` calling `assist`) and
recurse, or a read-only sub-agent could edit files.

# Rules

- Every LLM blocks the agent's entrypoints (`BLOCKED_ENTRYPOINTS`).[^constants]
- Read-only LLMs (`task` sub-agent, `suggest_github_fix`) also block `BLOCKED_DESTRUCTIVE`
  (`edit_file`, `write_file`, `suggest_github_pr_code_comment`); `suggest_github_fix` re-allows
  `suggest_github_pr_code_comment`, its only output channel.[^sub]
- `write_tests` additionally blocks build/test tools so the model writes tests instead of
  running them.
- **Only block functions that exist on the class.** Blocking a non-existent function raises
  `function "X" not found on type "Y"`, and listing absent functions makes the LLM aware of them
  and hallucinate calls.[^daggie-fix] [^system] That is why Daggie, Speck and Goose define their own
  entrypoint lists instead of the shared one.

[^constants]: agent_base/constants.py
[^daggie-fix]: fix(daggie): block only existing entrypoints to prevent LLM hallucination
[^sub]: fix: Block sub-agents tools
[^system]: Daggie system prompt, Blocked Functions
