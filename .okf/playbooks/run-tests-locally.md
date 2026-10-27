---
type: Playbook
title: "Run tests locally"
description: "Commands to run the workspace check and the tests module locally on Dagger 1.0, with and without GCP or LLM credentials."
tags: [playbook, testing]
generated: { by: claude-code/2.1.310, at: 2026-10-27T09:30:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: vertex-action
    resource: https://github.com/telchak/daggerverse/blob/main/.github/actions/vertex-ai-llm/action.yml
    title: ".github/actions/vertex-ai-llm/action.yml"
    author: human:telchak
    last_modified: 2026-10-27T09:30:00Z
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Run Tests Locally"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Development Setup and Testing"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/main.py
    title: "tests/src/tests/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

```bash
dagger check                                      # committed generated code matches `dagger generate`
dagger check -m ./tests --generated=false         # credential-free tests as checks: calver, health-check,
                                                  # oidc-token, angular, python-build, dagger-mcp
dagger api call -m ./tests all-no-credentials     # calver, health-check, oidc-token
dagger api call -m ./tests calver                 # one module
dagger api call -m ./tests semver --source=.      # semver needs the repo with history
dagger api call -m ./tests angular                # angular module, bundled fixture
GEMINI_API_KEY=... dagger api call -m ./tests monty-review   # one agent entrypoint (LLM)
```

To run an agent test the way CI does, on Vertex AI in the test project, use your own `gcloud`
login (it needs `roles/aiplatform.user` on the project) in place of the job's minted
token:[^vertex-action]

```bash
OPENAI_API_KEY=$(gcloud auth print-access-token) \
OPENAI_BASE_URL=https://aiplatform.googleapis.com/v1/projects/<project>/locations/global/endpoints/openapi \
OPENAI_MODEL=google/gemini-3.8-flash OPENAI_DISABLE_STREAMING=true \
  dagger api call -m ./tests monty-review
```

GCP tests need Workload Identity Federation inputs that only exist inside GitHub Actions
(`--oidc-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN --oidc-url=env:ACTIONS_ID_TOKEN_REQUEST_URL`,
plus provider, service account, project, region); a service account key can be passed with
`--credentials=env:GCP_SA_KEY`.[^readme] The function list is in `Tests`, or
`dagger api functions -m ./tests`.[^main] `dagger call` and `dagger functions` still work as
hidden aliases of the `dagger api` verbs.

Requirements: a container runtime and the Dagger CLI at the `DAGGER_VERSION` of `ci.yml`
(1.0.0-beta.21); the CLI starts an engine of its own version.[^contributing]

On a Windows host the root `dagger check` always fails: uploaded files get mode 0755 while the
generators write 0644, so every generated file looks changed. There, `dagger generate --no-apply`
showing no line changes is the local signal; see [known issues](/dagger/known-issues-1-0-beta.md).

[^readme]: Repository README, Run Tests Locally
[^contributing]: Contributing guide, Development Setup and Testing
[^main]: tests/src/tests/main.py
[^vertex-action]: .github/actions/vertex-ai-llm/action.yml
