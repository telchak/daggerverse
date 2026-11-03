---
type: Decision
title: "Gemini as the CI LLM provider"
description: "Agent tests in CI run on Gemini (GEMINI_API_KEY, vars.GEMINI_MODEL, gemini-3.8-flash since 2026-10-25) since 2026-02-17, after starting on Anthropic. Since 2026-10-27 the key belongs to the test project, whose billing account is on the Gemini API Prepay plan: a 402 means that prepaid balance is empty."
tags: [decision, ci, llm, billing]
generated: { by: claude-code/2.1.310, at: 2026-10-27T11:00:00Z }
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
    last_modified: 2026-10-27T10:30:00Z
  - id: signatures
    resource: https://github.com/dagger/dagger/commit/f13472409c1c450f8d5041fa9118b319151f78f7
    title: "fix(llm): keep Gemini signatures and call IDs"
    author: team:dagger
    last_modified: 2026-07-16T22:58:13Z
  - id: gemini3-issue
    resource: https://github.com/dagger/dagger/issues/14475
    title: "LLM integration crashes with Gemini 3.x: Function call is missing a thought_signature (dagger/dagger#14475, v0.21.8)"
    author: human:HeenaShaikh09
    last_modified: 2026-10-03T18:05:02Z
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
  - id: run-new-key
    resource: https://github.com/telchak/daggerverse/actions/runs/40484965303
    title: "CI run 40484965303: the test project's new key returned the same 402"
    author: process:github-actions
    last_modified: 2026-10-27T10:05:00Z
---

CI first configured `ANTHROPIC_MODEL` (2026-02-08)[^anthropic] and switched to Gemini on
2026-02-17.[^switch] Agents themselves are provider-agnostic (Dagger's `LLM` picks the provider
from env). Several prompt and helper workarounds target Gemini behaviour, see
[LLM results and fallbacks](/patterns/llm-output-binding.md). The commit message does not record
the reason for the switch.

# Model

The model is the repository variable `GEMINI_MODEL`, passed with `GEMINI_API_KEY` to every agent
job.[^ci] It was `gemini-2.5-flash` (set 2026-03-11), with Speck's jobs forced onto
`gemini-2.5-pro` "for better JSON output reliability". On 2026-10-25 the variable moved to
`gemini-3.8-flash` and the Speck override was removed: all agent tests now use the variable.

Gemini 3 attaches a thought signature to each function call, which must come back with the
history. Dagger's `google` provider has replayed it since 2026-07-16, a change the 1.0 betas
carry and 0.21.x does not.[^signatures] On 0.21.x a Gemini 3 model fails on its second tool call
with "Function call is missing a thought_signature".[^gemini3-issue]

# Key: the test project, on a Prepay balance

Since 2026-10-27 `GEMINI_API_KEY` is a Gemini API key created in the test project
(`dagger-tests`). The Gemini API's Prepay plan belongs to a billing account, not to a key or a
project,[^billing] and the account `dagger-tests` bills to is on it: the new key got the same 402
as the old one in its first run.[^run-new-key] The maintainer chose to top that balance up rather
than move the project to another billing account. Auto-reload, with a monthly cap, keeps CI's own
usage from draining it again.

Vertex AI usage of the same project is billed outside that plan: the Vertex route's first calls
went through that day. That route was dropped because Dagger's OpenAI client does not replay
thought signatures and Vertex no longer serves Gemini 2.5: see
[Vertex AI for the CI LLM](/decisions/vertex-ai-for-ci-llm.md) (deprecated).

# A 402 is the credit balance, not the model

Both keys draw on a Gemini API Prepay balance. Once the credits are used up, every key of every
project on that billing account fails with HTTP 402 until credits are added, whatever the model.
Nothing falls back to the free tier.[^billing] In CI, the agent's first LLM call fails with
`Error 402, Message: Your prepayment credits are depleted ... Status: RESOURCE_EXHAUSTED`,
surfacing as an `InvalidResultError` from the agent function.

The first 402 appeared on 2026-10-22; the last fully green run was on 2026-10-16. From then on
every agent job failed with it, on `gemini-2.5-flash` and, after the switch, on
`gemini-3.8-flash`, while the module tests passed.[^run] Changing `GEMINI_MODEL` does not help.
The fix is to buy credits on the AI Studio Billing page (minimum $5; optionally auto-reload with a
monthly cap), or to move the project to a billing account that is not on Prepay, then re-run the
failed jobs (`gh run rerun <run-id> --failed`). A new key on the same billing account does not
help.[^billing]

[^switch]: ci(github): Switch LLM provider variables from Anthropic to Gemini
[^anthropic]: fix: Add ANTHROPIC_MODEL variable to the Dagger workflow job
[^ci]: CI workflow
[^signatures]: fix(llm): keep Gemini signatures and call IDs
[^gemini3-issue]: LLM integration crashes with Gemini 3.x: Function call is missing a thought_signature (dagger/dagger#14475, v0.21.8)
[^billing]: Gemini API billing (Prepay plan)
[^run]: CI run 40175567184: every agent job failed with HTTP 402 on gemini-3.8-flash
[^run-new-key]: CI run 40484965303: the test project's new key returned the same 402
