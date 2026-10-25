---
type: Decision
title: "Gemini as the CI LLM provider"
description: "Agent tests in CI run on Gemini (GEMINI_API_KEY, vars.GEMINI_MODEL, gemini-3.8-flash since 2026-10-25) since 2026-02-17, after starting on Anthropic."
tags: [decision, ci, llm]
generated: { by: claude-code/2.1.310, at: 2026-10-25T09:00:00Z }
stale_after: 2027-04-25T00:00:00Z
sources:
  - id: switch
    resource: https://github.com/telchak/daggerverse/commit/01786d33b104b74982a26f6ae0def585acc57f66
    title: "ci(github): Switch LLM provider variables from Anthropic to Gemini"
    author: human:telchak
    last_modified: 2026-02-17T22:26:48+01:00
  - id: anthropic
    resource: https://github.com/telchak/daggerverse/commit/58ee9532e8d7452af356b69c421ae9ce735b527a
    title: "fix: Add ANTHROPIC_MODEL variable to the Dagger workflow job"
    author: human:telchak
    last_modified: 2026-02-08T18:33:31+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-25T09:00:00Z
---

CI first configured `ANTHROPIC_MODEL` (2026-02-08)[^anthropic] and switched to Gemini on
2026-02-17.[^switch] Agents themselves are provider-agnostic (Dagger's `LLM` picks the provider
from env). Several prompt and helper workarounds target Gemini behaviour, see
[LLM results and fallbacks](/patterns/llm-output-binding.md). The commit message does not record
the reason for the switch.

The model is the repository variable `GEMINI_MODEL`, passed to every agent job.[^ci] It was
`gemini-2.5-flash` (set 2026-03-11), with Speck's jobs forced onto `gemini-2.5-pro` "for better
JSON output reliability". On 2026-10-25 both 2.5 models stopped serving the CI project (every
agent job failed), so the variable moved to `gemini-3.8-flash` and the Speck override was
removed: all agent tests now use the variable.

[^switch]: ci(github): Switch LLM provider variables from Anthropic to Gemini
[^anthropic]: fix: Add ANTHROPIC_MODEL variable to the Dagger workflow job
[^ci]: CI workflow
