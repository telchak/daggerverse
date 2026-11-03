---
type: Design Pattern
title: "LLM results and fallbacks"
description: "How agents read results in Dagger 1.0 (final reply or edited workspace, after loop), the JSON replies of routers and suggest-fix, and the retry when a routed call changes nothing; formerly Env output bindings."
tags: [agent, llm, pattern, gotcha, gemini]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: llm
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/llm_helpers.py
    title: "agent_base/llm_helpers.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: routing
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/routing.py
    title: "agent_base/routing.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: gh
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/github_tools.py
    title: "agent_base/github_tools.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
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

# History (0.x)

With `env.with_string_output("result", ...)` the model was expected to call the output binding
tool. In practice (notably Gemini, the CI model) it sometimes answered in plain text and never set
the binding, or described code instead of calling `write_file`.[^binding] [^write-file] The fix was
a prompt rule and `get_result_or_last_reply`, which fell back to `last_reply()`.[^helper]

# Dagger 1.0

`Env` and its outputs are gone, so the fallback became the design: a result is the model's
**final reply** or the **workspace it edited**.

- String entrypoints return `llm_helpers.reply(llm)` = `llm.loop().last_reply()`; directory
  entrypoints return `edited_directory(llm)` = `llm.loop().workspace().directory("/")`.[^llm]
  `last_reply()` and `workspace()` do not run the loop themselves, so always go through these
  helpers.
- Prompts say "Your final reply is your result" and describe inputs under `## Inputs`; the values
  are appended under `## Input values` (`format_inputs`).[^llm]
- The router and suggest-fix prompts ask for a JSON reply; `routing.extract_json_object` accepts a
  bare, fenced or embedded object, a malformed router reply falls back to `assist`, and
  `parse_suggestions` keeps at most 5 well-formed suggestions.[^routing] [^gh]
- `execute_routed_function` compares directory digests before and after and re-runs the routed
  function once, with a retry note in the prompt, if the workspace is unchanged.[^routing]
- `develop_github_issue` comments on the issue and raises when the PR would have no changes.

[^llm]: agent_base/llm_helpers.py
[^routing]: agent_base/routing.py
[^gh]: agent_base/github_tools.py
[^binding]: fix: fix LLM output binding in agent prompts
[^helper]: fix: Add get_result_or_last_reply helper function
[^write-file]: fix: Fix agent write_file issue
