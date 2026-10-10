---
type: Playbook
title: "Run tests locally"
description: "Commands to run the tests module locally, with and without GCP or LLM credentials."
tags: [playbook, testing]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Run Tests Locally"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/main.py
    title: "tests/src/tests/main.py"
    author: human:telchak
    last_modified: 2026-10-10T14:03:13+00:00
---

```bash
dagger -m tests call all-no-credentials           # calver, health-check, oidc-token, semver
dagger -m tests call calver                       # one module
dagger -m tests call semver --source=.            # semver needs the repo with history
dagger -m tests call angular                      # angular module, bundled fixture
GEMINI_API_KEY=... dagger -m tests call monty-review   # one agent entrypoint (LLM)
```

GCP tests need Workload Identity Federation inputs that only exist inside GitHub Actions
(`--oidc-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN --oidc-url=env:ACTIONS_ID_TOKEN_REQUEST_URL`,
plus provider, service account, project, region); a service account key can be passed with
`--credentials=env:GCP_SA_KEY`.[^readme] The function list is in `Tests`.[^main]

A Dagger engine (container runtime) and the CLI matching `engineVersion` are required.

[^readme]: Repository README, Run Tests Locally
[^main]: tests/src/tests/main.py
