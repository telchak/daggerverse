---
type: Decision
title: "Vertex AI for the CI LLM"
description: "Deprecated on 2026-10-27, the day it was tried: Gemini 3 on Vertex AI's OpenAI-compatible endpoint needs thought signatures that Dagger 1.0's OpenAI client drops, and Vertex no longer serves Gemini 2.5. Replaced by a Gemini API key of the test project."
tags: [decision, ci, llm, gcp, vertex-ai]
status: deprecated
generated: { by: claude-code/2.1.310, at: 2026-10-27T10:30:00Z }
stale_after: 2027-01-27T00:00:00Z
sources:
  - id: action
    resource: https://github.com/telchak/daggerverse/blob/4de9e51d1688d96bda2eb85b2324c5e448c52c3d/.github/actions/vertex-ai-llm/action.yml
    title: ".github/actions/vertex-ai-llm/action.yml at 4de9e51"
    author: human:telchak
    last_modified: 2026-10-27T09:30:00Z
  - id: run
    resource: https://github.com/telchak/daggerverse/actions/runs/40479648670
    title: "CI run 40479648670: Vertex AI reached, second tool call rejected for a missing thought_signature"
    author: process:github-actions
    last_modified: 2026-10-27T09:40:00Z
  - id: openai-client
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/llm_openai.go
    title: "Dagger engine: the openai provider's client (core/llm_openai.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: google-client
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/llm_google.go
    title: "Dagger engine: the google provider's client (core/llm_google.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: signatures
    resource: https://github.com/dagger/dagger/commit/f13472409c1c450f8d5041fa9118b319151f78f7
    title: "fix(llm): keep Gemini signatures and call IDs"
    author: team:dagger
    last_modified: 2026-07-16T22:58:13Z
  - id: versions
    resource: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
    title: "Vertex AI: model versions and lifecycle"
    author: team:google
    last_modified: 2026-10-27T10:30:00Z
  - id: vertex-issue
    resource: https://github.com/dagger/dagger/issues/11203
    title: "Support the Google Vertex AI APIs (dagger/dagger#11203)"
    author: human:ciarand
    last_modified: 2026-03-25T05:18:11Z
---

# Status

Deprecated on 2026-10-27, the day it was tried. It works up to the model's first tool call, then
fails. Replaced by a Gemini API key of the test project, billed to it: see
[Gemini as the CI LLM provider](/decisions/gemini-as-ci-llm.md).

# What was tried

After the AI Studio key's Prepay balance ran out, the agent jobs were to run Gemini on Vertex AI
in the test project (`GCP_PROJECT_ID`, `dagger-tests`), billed to it. Dagger 1.0 has no Vertex
backend,[^vertex-issue] so a local action, `.github/actions/vertex-ai-llm`, pointed the `openai`
provider at Vertex's OpenAI-compatible endpoint.[^action] It exchanged the job's OIDC token at
Google STS, impersonated `GCP_SERVICE_ACCOUNT` for a one-hour token, masked it, and exported the
following:

- `OPENAI_API_KEY`: that token;
- `OPENAI_BASE_URL`: `https://aiplatform.googleapis.com/v1/projects/<project>/locations/global/endpoints/openapi`;
- `OPENAI_MODEL`: `google/<vars.GEMINI_MODEL>`, which also made `openai` the default provider (a
  `google/` name would otherwise route to the `google` provider);
- `OPENAI_DISABLE_STREAMING`: `true`.

# Why it failed

- Authentication and routing worked. The step succeeded in every job, and the requests reached
  Vertex.[^run]
- Gemini 3 attaches a thought signature to each function call, and expects it back with the
  history. Through the OpenAI-compatible API it travels as
  `extra_content.google.thought_signature` on the tool call.
- Dagger's OpenAI client keeps only a tool call's id, name and arguments, both when it reads a
  reply and when it sends the history.[^openai-client] The second request fails with 400
  INVALID_ARGUMENT, "Function call is missing a thought_signature in functionCall parts".[^run]
- Dagger's `google` provider does keep signatures (since 2026-07-16),[^signatures] but it only
  talks to the Gemini API, with a key.[^google-client]
- No older model avoids the problem. Vertex retired Gemini 2.5 Pro, Flash and Flash-Lite on
  2026-10-20, and every Gemini it still serves is 3.x or later.[^versions]

# To revive it

Restore the action and its step from 4de9e51 once a Dagger release replays the signature through
its OpenAI client, or gains a Vertex backend. The routing rule and the streaming choice above
still apply.

[^action]: .github/actions/vertex-ai-llm/action.yml at 4de9e51
[^run]: CI run 40479648670: Vertex AI reached, second tool call rejected for a missing thought_signature
[^openai-client]: Dagger engine: the openai provider's client (core/llm_openai.go)
[^google-client]: Dagger engine: the google provider's client (core/llm_google.go)
[^signatures]: fix(llm): keep Gemini signatures and call IDs
[^versions]: Vertex AI: model versions and lifecycle
[^vertex-issue]: Support the Google Vertex AI APIs (dagger/dagger#11203)
