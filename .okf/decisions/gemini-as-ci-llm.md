---
type: Decision
title: "Gemini as the CI LLM provider"
description: "Agent tests in CI run on Gemini (vars.GEMINI_MODEL, gemini-3.8-flash since 2026-10-25) since 2026-02-17, after starting on Anthropic: through an AI Studio GEMINI_API_KEY on a Prepay balance (a 402 means it is empty) until 2026-10-27, then through Vertex AI in the test project."
tags: [decision, ci, llm, billing]
generated: { by: claude-code/2.1.310, at: 2026-10-27T09:30:00Z }
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
  - id: billing
    resource: https://ai.google.dev/gemini-api/docs/billing
    title: "Gemini API billing (Prepay plan)"
    author: team:google
    last_modified: 2026-10-27T08:45:32Z
  - id: run
    resource: https://github.com/telchak/daggerverse/actions/runs/40175567184
    title: "CI run 40175567184: every agent job failed with HTTP 402 on gemini-3.8-flash"
    author: process:github-actions
    last_modified: 2026-10-25T08:19:06Z
---

CI first configured `ANTHROPIC_MODEL` (2026-02-08)[^anthropic] and switched to Gemini on
2026-02-17.[^switch] Agents themselves are provider-agnostic (Dagger's `LLM` picks the provider
from env). Several prompt and helper workarounds target Gemini behaviour, see
[LLM results and fallbacks](/patterns/llm-output-binding.md). The commit message does not record
the reason for the switch.

The model is the repository variable `GEMINI_MODEL`, passed to every agent job.[^ci] It was
`gemini-2.5-flash` (set 2026-03-11), with Speck's jobs forced onto `gemini-2.5-pro` "for better
JSON output reliability". On 2026-10-25 the variable moved to `gemini-3.8-flash` and the Speck
override was removed: all agent tests now use the variable.

Since 2026-10-27 the jobs reach that model through Vertex AI in the test project, billed to it,
instead of the AI Studio key: see [Vertex AI for the CI LLM](/decisions/vertex-ai-for-ci-llm.md).
The next section is about the key it replaced, which local runs can still use.

# Billing of the AI Studio key: a 402 is the credit balance, not the model

The key draws on a Gemini API Prepay balance. Once the credits are used up, every key of every
project on that billing account fails with HTTP 402 until credits are added, whatever the model,
and nothing falls back to the free tier.[^billing] In CI, the agent's first LLM call fails with
`Error 402, Message: Your prepayment credits are depleted ... Status: RESOURCE_EXHAUSTED`,
surfacing as an `InvalidResultError` from the agent function. The first 402 appeared on
2026-10-22 (the last fully green run was on 2026-10-16). From then on every agent job failed with
it, on `gemini-2.5-flash` and, after the switch, on `gemini-3.8-flash`, while the module tests
passed.[^run] The switch was made in the belief that the 2.5 models had been retired. The 402
does not support that belief, and it answers before any model check could.

To recover, buy credits on the AI Studio Billing page (minimum $5; card payments clear almost
at once, then the balance takes a short while to update). Optionally enable auto-reload, with a
monthly cap, so CI's own usage cannot drain the balance again. Then re-run the failed jobs
(`gh run rerun <run-id> --failed`). Changing `GEMINI_MODEL` does not help.[^billing]

[^switch]: ci(github): Switch LLM provider variables from Anthropic to Gemini
[^anthropic]: fix: Add ANTHROPIC_MODEL variable to the Dagger workflow job
[^ci]: CI workflow
[^billing]: Gemini API billing (Prepay plan)
[^run]: CI run 40175567184: every agent job failed with HTTP 402 on gemini-3.8-flash
