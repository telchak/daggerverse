---
type: Reference
title: "Running Dagger in GitHub Actions"
description: "How this repo and Daggie-generated workflows call Dagger from GitHub Actions: dagger-for-github inputs, version pinning, OIDC env passthrough."
tags: [dagger, ci, github-actions]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, GitHub Actions Integration"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
  - id: gha
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/getting-started/ci-integrations/github-actions.mdx
    title: "Dagger docs: GitHub Actions (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
---

- Use `dagger/dagger-for-github` (here `@v8.4.1`), never a curl install.[^daggie] Its inputs are
  `version`, `verb`, `args` (this repo also passes `cloud-token`).[^ci] `version` must equal the
  `engineVersion` in `dagger.json` without the `v`.
- This repo uses the action with `verb: version` only to install the CLI, then runs
  `dagger call -m tests ...` in shell steps to post-process output.[^ci]
- Secrets go in as `env:VAR` arguments (`--oidc-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN`); GCP
  OIDC needs `permissions: id-token: write`.
- Calling a published agent from another repo:
  `args: -m github.com/telchak/daggerverse/monty@monty/vX.Y.Z --source=. suggest-github-fix ...`.[^gha]

[^ci]: CI workflow
[^daggie]: Daggie system prompt, GitHub Actions Integration
[^gha]: Dagger docs: GitHub Actions (v0.21.10)
