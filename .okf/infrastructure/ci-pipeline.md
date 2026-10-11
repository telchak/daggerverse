---
type: CI Pipeline
title: "CI pipeline (ci.yml)"
description: "The single GitHub Actions workflow: discover modules and agents, validate, test each in a parallel matrix on self-hosted Dagger runners, then release."
tags: [ci, github-actions]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: ".github/workflows/ci.yml"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
  - id: single
    resource: https://github.com/telchak/daggerverse/commit/183ab8e60066d822711d12cc2fba0a7b231e6bc6
    title: "refactor: replace 3 workflows with single ci.yml"
    author: human:telchak
    last_modified: 2025-12-31T18:25:34+01:00
  - id: matrix
    resource: https://github.com/telchak/daggerverse/commit/c5edb0392b429535583e55458ca26f73cc885921
    title: "refactor: unify test jobs with auto-discovered matrix"
    author: human:telchak
    last_modified: 2026-01-04T21:09:31+01:00
  - id: arc
    resource: https://github.com/telchak/daggerverse/commit/432fe2f2187ad81bc2538dd9a14c3d212436a7fb
    title: "ci(github-actions): Add ARC GitHub Runners to CI workflow"
    author: human:telchak
    last_modified: 2026-03-31T19:10:13+02:00
  - id: gemini
    resource: https://github.com/telchak/daggerverse/commit/01786d33b104b74982a26f6ae0def585acc57f66
    title: "ci(github): Switch LLM provider variables from Anthropic to Gemini"
    author: human:telchak
    last_modified: 2026-02-17T22:26:48+01:00
---

# Triggers

Push to `main`, pull requests to `main`, and `workflow_dispatch` (input `dry_run`).
`DAGGER_VERSION` env pins the CLI (`0.21.10` at the time of writing); jobs other than `discover`
run on the self-hosted runner label `dagger-v<version>`.[^ci]

# Jobs

| Job | Runs on | Does |
|-----|---------|------|
| `discover` | ubuntu-latest | `find . -maxdepth 2 -name dagger.json` (excluding `tests/`); a module with `src/*/prompts/` is an **agent**; builds `agent_tests` as `<agent>-<suffix>` from `.agent-tests` or the default `assist review write-tests build upgrade` |
| `validate` | dagger runner | per module: `dagger.json` exists and has `description`, `README.md` and `examples/` exist (errors); `dagger functions` loads; `.py/.ts/.go` files over **600 lines** produce a warning in the summary |
| `test-modules` | dagger runner, matrix | `dagger call -m tests <module> $ARGS`; `gcp-*` modules get OIDC/WIF args, `--region=europe-west9`, and `--credentials=env:GCP_SA_KEY` when set; `gcp-artifact-registry` gets `--repository`, `semver` gets `--source=.` |
| `test-agents` | dagger runner, matrix, 20 min timeout | `dagger call -m tests <agent>-<test>`; agents with `.agent-gcp` get GCP args (+ `--developer-knowledge-api-key`); `speck-*` forces `GEMINI_MODEL=gemini-2.5-pro` |
| `test-angie-github-issue` | dagger runner | real issue-to-PR run, then closes the PR |
| `release` | dagger runner, `main` only, not PRs | per-module semver tags, see [release process](/infrastructure/release-process.md) |

Test output lines matching `[OK]`, `[!!]`, `[--]` (or legacy `PASS:`/`FAIL:`) are copied into
the job summary.[^ci]

# Secrets and variables

`DAGGER_CLOUD_TOKEN`, `GEMINI_API_KEY` + `vars.GEMINI_MODEL` (the CI LLM, switched from
Anthropic to Gemini on 2026-02-17[^gemini]), `GCP_WORKLOAD_IDENTITY_PROVIDER`,
`GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_ARTIFACT_REGISTRY_REPOSITORY`, `GCP_SA_KEY`
(optional), `GCP_DEVELOPER_KNOWLEDGE_API_KEY`, `ANGIE_TEST_GITHUB_TOKEN`. GCP auth uses GitHub
OIDC (`id-token: write`), see the
[native OIDC decision](/decisions/native-oidc-instead-of-google-github-actions-auth.md).

# History

Three workflows merged into one on 2025-12-31;[^single] auto-discovered matrix on
2026-01-04;[^matrix] self-hosted ARC runners labelled `dagger-v*` replaced `ubuntu-latest` plus
docker-volume engine caching on 2026-03-10.[^arc] See the
[runners decision](/decisions/self-hosted-dagger-runners.md).

# Gotcha

`OUTPUT=$(dagger call ... 2>&1)` buffers all output; when a step hits its timeout the buffer and
any traceback are lost. See [debug an agent CI timeout](/playbooks/debug-agent-ci-timeout.md).

[^ci]: .github/workflows/ci.yml
[^single]: refactor: replace 3 workflows with single ci.yml
[^matrix]: refactor: unify test jobs with auto-discovered matrix
[^arc]: ci(github-actions): Add ARC GitHub Runners to CI workflow
[^gemini]: ci(github): Switch LLM provider variables from Anthropic to Gemini
