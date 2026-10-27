---
type: CI Pipeline
title: "CI pipeline (ci.yml)"
description: "The single GitHub Actions workflow: discover modules and agents, validate them, check the committed generated code, test each in a parallel matrix on self-hosted Dagger runners, then release."
tags: [ci, github-actions]
generated: { by: claude-code/2.1.310, at: 2026-10-27T11:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: ".github/workflows/ci.yml"
    author: human:telchak
    last_modified: 2026-10-27T10:30:00Z
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

# Triggers and environment

Push to `main`, pull requests to `main`, and `workflow_dispatch` (input `dry_run`).[^ci]

- `DAGGER_VERSION: "1.0.0-beta.21"` pins the CLI, which starts an engine of its own version.
- `DAGGER_PROGRESS: plain`: outside a TTY the 1.0 CLI defaults to the one-shot `report`
  progress; `plain` streams logs.
- Every job except `discover` runs on the self-hosted runner label `dagger-v1.0.0-beta.21`; the
  ARC runner scale set with that label must exist, or the jobs queue forever.
- `dagger/dagger-for-github@v8.4.1` only installs the CLI (`version`, `cloud-token`). It is not
  given `verb: version`, which runs `dagger --progress plain version`, rejected by the 1.0 CLI.[^ci]

# Jobs

| Job | Needs | Runs on | Does |
|-----|-------|---------|------|
| `discover` | | ubuntu-latest | `find . -maxdepth 2 -name dagger-module.toml` (excluding `tests/`); a module with `src/*/prompts/` is an **agent**; builds `agent_tests` as `<agent>-<suffix>` from `.agent-tests` or the default `assist review write-tests build upgrade` |
| `validate` | discover | dagger runner | per module and agent, errors: no `dagger-module.toml`; an empty description (the first docstring line of `src/*/__init__.py`, read with awk); no `README.md` or `examples/`; `dagger api functions -m ./<module>` fails (a module that does not load is now an error). `.py/.ts/.go` files over **600 lines** produce a warning in the summary |
| `check` | discover | dagger runner | `dagger check` at the root: the Python SDK staleness checks, so every module's committed `sdk/`, `clients/` and entrypoint types must match what `dagger generate` writes |
| `test-modules` | discover, validate | dagger runner, matrix | `dagger api call -m ./tests <module> $ARGS`; `gcp-*` modules get OIDC/WIF args, `--region=europe-west9`, and `--credentials=env:GCP_SA_KEY` when set; `gcp-artifact-registry` gets `--repository`, `semver` gets `--source=.` |
| `test-agents` | discover, validate | dagger runner, matrix, 20 min timeout | `dagger api call -m ./tests <agent>-<test>`; agents with `.agent-gcp` get GCP args (+ `--developer-knowledge-api-key`) |
| `test-angie-github-issue` | validate | dagger runner | real issue-to-PR run (`angie-develop-github-issue`), then closes the PR |
| `release` | discover, check, test-modules, test-agents, test-angie-github-issue | dagger runner, `main` only, not PRs | `dagger api call -m ./semver release ...` per changed module, see [release process](/infrastructure/release-process.md) |

Test output lines matching `[OK]`, `[!!]`, `[--]` (or legacy `PASS:`/`FAIL:`) are copied into
the job summary.[^ci] The tests module's own checks (`dagger check -m ./tests`) are not run by CI;
`test-modules` runs the same tests, see [tests module](/infrastructure/tests-module.md).

# Secrets and variables

`DAGGER_CLOUD_TOKEN`, `GEMINI_API_KEY` + `vars.GEMINI_MODEL` (`gemini-3.8-flash`; the CI LLM,
read by the two agent jobs only, switched from Anthropic to Gemini on 2026-02-17[^gemini]),
`GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`,
`GCP_ARTIFACT_REGISTRY_REPOSITORY`, `GCP_SA_KEY` (optional), `GCP_DEVELOPER_KNOWLEDGE_API_KEY`,
`ANGIE_TEST_GITHUB_TOKEN`. GCP auth uses GitHub OIDC (`id-token: write`), see the
[native OIDC decision](/decisions/native-oidc-instead-of-google-github-actions-auth.md).

Since 2026-10-27 `GEMINI_API_KEY` is a key of the test project. Its billing account is on the
Gemini API Prepay plan, so CI spends a prepaid balance, and every agent job fails with 402 once it
is empty. See [Gemini as the CI LLM provider](/decisions/gemini-as-ci-llm.md), and
[Vertex AI for the CI LLM](/decisions/vertex-ai-for-ci-llm.md) (deprecated) for why the jobs do
not call Vertex AI.

# History

Three workflows merged into one on 2025-12-31;[^single] auto-discovered matrix on
2026-01-04;[^matrix] self-hosted ARC runners labelled `dagger-v*` replaced `ubuntu-latest` plus
docker-volume engine caching on 2026-03-10.[^arc] See the
[runners decision](/decisions/self-hosted-dagger-runners.md). The
[Dagger 1.0 migration](/decisions/migrate-to-dagger-1-0.md) added the `check` job, discovery by
`dagger-module.toml`, the docstring description rule and `dagger api call`.

# Gotchas

- `OUTPUT=$(dagger api call ... 2>&1)` buffers all output, the `plain` progress included; when a
  step hits its timeout the buffer and any traceback are lost. See
  [debug an agent CI timeout](/playbooks/debug-agent-ci-timeout.md).
- A Renovate engine bump fails `check` until `dagger generate -y`, run with the new CLI, is pushed
  onto the PR; see [Renovate](/infrastructure/renovate.md).
- The `plain` progress prints every exec's stdout, and this repository's logs are public.
  GitHub masks the secrets it knows about, and the OIDC token it issued, but not a credential minted
  from them. Until 2026-10-27, `test-modules (gcp-auth)` and `(gcp-firebase)` printed live GCP
  access tokens that way. A credential must never be an exec's stdout; see the
  [Python SDK conventions](/conventions/python-sdk.md).
- A job can die before any test runs, with `grpc: the client connection is closing`,
  `no active session attachables ... context deadline exceeded`, or `kubectl ... exec ...
  buildctl dial-stdio ... exited with exit status 1`. That is the CLI losing its kubectl-exec
  link to the single shared engine. It happened on 2026-10-27 when node `raphael` briefly went
  NotReady (13 jobs), then once more with all nodes Ready. Re-run the failed jobs; the same code
  passed on retry.

[^ci]: .github/workflows/ci.yml
[^single]: refactor: replace 3 workflows with single ci.yml
[^matrix]: refactor: unify test jobs with auto-discovered matrix
[^arc]: ci(github-actions): Add ARC GitHub Runners to CI workflow
[^gemini]: ci(github): Switch LLM provider variables from Anthropic to Gemini
