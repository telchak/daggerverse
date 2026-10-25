---
type: Reference
title: "Running Dagger in GitHub Actions"
description: "How this repo and Daggie-generated workflows call Dagger 1.0 from GitHub Actions: dagger-for-github inputs, version pinning, progress output, LLM access, OIDC env passthrough."
tags: [dagger, ci, github-actions]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, GitHub Actions Integration"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: cloud-checks
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/getting-started/cloud-checks.mdx
    title: "Dagger docs: Set up Cloud Checks (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
---

- Use `dagger/dagger-for-github` (here `@v8.4.1`), never a curl install. Its inputs include
  `version`, `verb`, `args`, `module`, `workdir`, `cloud-token`, `dagger-flags`.[^daggie]
- `version` pins the CLI, which starts an engine of the same version: for a 1.0 workspace use the
  version the generated code was made with (`"1.0.0-beta.21"`, no `v`). Self-hosted runners must
  serve the same engine version.
- Do not use `verb: version`: the action runs `dagger --progress plain version`, which 1.0
  rejects. With no `verb` the action only installs the CLI; `verb: check` runs `dagger check`.[^daggie]
- Outside a TTY, 1.0 prints a one-shot report by default; this repo sets `DAGGER_PROGRESS: plain`
  so a step that times out still shows where it was.[^ci]
- This repo installs the CLI with the action, then runs `dagger check` and
  `dagger api call -m ./tests ...` in shell steps to post-process output.[^ci]
- Secrets go in as `env:VAR` arguments (`--oidc-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN`); GCP
  OIDC needs `permissions: id-token: write`.
- A module loaded from a Git ref that calls an LLM needs `--allow-llm=<ref>` (or `all`), or
  `DAGGER_ALLOW_LLM`, in non-interactive CI. Calling a published agent from another repo:
  `verb: call`, `args: --allow-llm=all -m github.com/telchak/daggerverse/monty@<version> --source=. suggest-github-fix ...`
  (`verb: call` runs `dagger call`, the hidden 0.x name of `dagger api call`).[^daggie]
- Without a workflow at all, Cloud Checks (`dagger cloud checks on`) run the workspace's checks on
  every push and pull request.[^cloud-checks]

[^ci]: CI workflow
[^daggie]: Daggie system prompt, GitHub Actions Integration
[^cloud-checks]: Dagger docs: Set up Cloud Checks (v1.0.0-beta.21)
