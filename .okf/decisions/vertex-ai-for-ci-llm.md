---
type: Decision
title: "Vertex AI for the CI LLM"
description: "Agent tests reach Gemini on Vertex AI in the test project, billed to it, through Dagger's openai provider and Vertex's OpenAI-compatible endpoint, with a one-hour token minted from the job's OIDC token. Replaces the AI Studio GEMINI_API_KEY on 2026-10-27."
tags: [decision, ci, llm, gcp, vertex-ai]
status: draft
generated: { by: claude-code/2.1.310, at: 2026-10-27T09:30:00Z }
stale_after: 2027-01-27T00:00:00Z
sources:
  - id: action
    resource: https://github.com/telchak/daggerverse/blob/main/.github/actions/vertex-ai-llm/action.yml
    title: ".github/actions/vertex-ai-llm/action.yml"
    author: human:telchak
    last_modified: 2026-10-27T09:30:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-27T09:30:00Z
  - id: google-client
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/llm_google.go
    title: "Dagger engine: the google provider's client (core/llm_google.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: router
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/llm_router.go
    title: "Dagger engine: LLM routing (core/llm_router.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: wire
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/internal/cmd/dagger/llmconfig/wire.go
    title: "Dagger CLI: LLM configuration from the environment (llmconfig/wire.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: openai-client
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/llm_openai.go
    title: "Dagger engine: the openai provider's client (core/llm_openai.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: vertex-issue
    resource: https://github.com/dagger/dagger/issues/11203
    title: "Support the Google Vertex AI APIs (dagger/dagger#11203)"
    author: human:ciarand
    last_modified: 2026-03-25T05:18:11Z
  - id: vertex-openai
    resource: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/migrate/openai/auth-and-credentials
    title: "Google Cloud: OpenAI libraries with Gemini on Vertex AI, authentication"
    author: team:google
    last_modified: 2026-10-27T09:30:00Z
---

# Context

On 2026-10-22 the AI Studio key that CI used ran out of Prepay credits, and every agent job
failed with HTTP 402 (see [Gemini as the CI LLM provider](/decisions/gemini-as-ci-llm.md)). The
GCP project the module tests use (`GCP_PROJECT_ID`, `dagger-tests`) is billed to a card and
already has Vertex AI enabled: the `gcp-vertex-ai` test lists its models and endpoints with CI's
identity. The LLM belongs there.

Dagger 1.0 has no Vertex AI backend. Its `google` provider builds the genai client from an API
key alone,[^google-client] and the request for Vertex support became a discussion on
2026-03-25.[^vertex-issue]

# Decision

Each agent job runs the local action `vertex-ai-llm` before `dagger api call`.[^ci] The action
exchanges the job's GitHub OIDC token at Google STS, impersonates `GCP_SERVICE_ACCOUNT` for a
one-hour `cloud-platform` token, masks every token it handles, and exports the following:[^action]

- `OPENAI_API_KEY`: the access token, which Vertex accepts as the OpenAI key;[^vertex-openai]
- `OPENAI_BASE_URL`: `https://aiplatform.googleapis.com/v1/projects/<project>/locations/global/endpoints/openapi`;
- `OPENAI_MODEL`: `google/<vars.GEMINI_MODEL>`;
- `OPENAI_DISABLE_STREAMING`: `true`.

`OPENAI_MODEL` does more than name the model. The CLI turns the first exported `*_MODEL` into the
configuration's default provider and model,[^wire] so `dag.llm()` routes to `openai`. Without
that, a `google/...` or `gemini-...` name is routed by its prefix to the `google` provider, which
has no key here.[^router] An explicit `llm(model: "google/...")` would still go that way; no agent
passes one.

The token is minted in the runner's shell, not by `gcp-auth`. The key must be in the CLI's
environment before the call, and a token minted by a Dagger function passes through an exec's
stdout, which Dagger logs: the module tests printed live tokens in this public repository's logs
until 2026-10-27. This one credential departs from the
[native OIDC decision](/decisions/native-oidc-instead-of-google-github-actions-auth.md); the
modules keep their Dagger-native OIDC.

Streaming is off because the agents always pass tools. With tools, Dagger's OpenAI client then
takes its non-streaming path, and a turn's tool calls arrive whole rather than reassembled from
streamed deltas by index.[^openai-client]

# Consequences

- The test project must let the service account call models: `roles/aiplatform.user`, or at least
  `aiplatform.endpoints.predict`. This could not be checked from outside CI; without it, the
  first LLM call fails with 403.
- The token lasts an hour, and the agent test step times out at 20 minutes.
- CI no longer reads `GEMINI_API_KEY`; the repository secret can go. Local runs can keep using
  one, or take CI's route with `gcloud auth print-access-token`, see
  [run tests locally](/playbooks/run-tests-locally.md).
- Vertex ignores the OpenAI parameters it does not support, such as `stream_options`.
- Draft until a CI run on this route is green.

[^action]: .github/actions/vertex-ai-llm/action.yml
[^ci]: CI workflow
[^google-client]: Dagger engine: the google provider's client (core/llm_google.go)
[^router]: Dagger engine: LLM routing (core/llm_router.go)
[^wire]: Dagger CLI: LLM configuration from the environment (llmconfig/wire.go)
[^openai-client]: Dagger engine: the openai provider's client (core/llm_openai.go)
[^vertex-issue]: Support the Google Vertex AI APIs (dagger/dagger#11203)
[^vertex-openai]: Google Cloud: OpenAI libraries with Gemini on Vertex AI, authentication
