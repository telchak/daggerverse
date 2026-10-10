---
type: Design Pattern
title: "LLM output binding and fallbacks"
description: "Agents declare a `result` output on the Env and must make the model set it; helpers fall back to last_reply, and routed calls retry when nothing changed."
tags: [agent, llm, pattern, gotcha, gemini]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: llm
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/llm_helpers.py
    title: "agent_base/llm_helpers.py"
    author: human:telchak
    last_modified: 2026-02-28T16:53:12+01:00
  - id: routing
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/routing.py
    title: "agent_base/routing.py"
    author: human:telchak
    last_modified: 2026-02-21T18:58:15+01:00
  - id: binding
    resource: https://github.com/telchak/daggerverse/commit/a759012644d6a45dbb5e139e746a48d2ee9d02cf
    title: "fix: fix LLM output binding in agent prompts"
    author: human:telchak
    last_modified: 2026-02-21T17:12:34+01:00
  - id: helper
    resource: https://github.com/telchak/daggerverse/commit/6189095df60a409eac4e78fa89bac0154c98c160
    title: "fix: Add get_result_or_last_reply helper function"
    author: human:telchak
    last_modified: 2026-02-22T02:17:19+01:00
  - id: write-file
    resource: https://github.com/telchak/daggerverse/commit/a34cdac935fba02b87367e6615513fddafd4ddc7
    title: "fix: Fix agent write_file issue"
    author: human:telchak
    last_modified: 2026-02-21T17:39:03+01:00
---

# Problem

With `env.with_string_output("result", ...)`, the model is expected to call the output binding
tool. In practice (notably Gemini, the CI model) it sometimes answers in plain text and never
sets the binding, or describes code instead of calling `write_file`.[^binding] [^write-file]

# Mitigations in place

1. Prompts say explicitly: "When a `result` output is declared ... you MUST explicitly set it".
2. `get_result_or_last_reply(work)` reads the binding and falls back to `work.last_reply()`.[^helper] [^llm]
3. `execute_routed_function` compares directory digests before/after and re-runs the routed
   function once if the workspace is unchanged.[^routing]
4. `develop_github_issue` comments on the issue and raises when the PR would have no changes
   ("nothing to commit").

When adding a new string-returning entrypoint, use `get_result_or_last_reply` rather than
reading the output directly.

[^llm]: agent_base/llm_helpers.py
[^routing]: agent_base/routing.py
[^binding]: fix: fix LLM output binding in agent prompts
[^helper]: fix: Add get_result_or_last_reply helper function
[^write-file]: fix: Fix agent write_file issue
