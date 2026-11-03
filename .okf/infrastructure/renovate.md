---
type: Configuration
title: "Renovate configuration"
description: "Renovate bumps the Dagger version in CI (DAGGER_VERSION, runner labels), the README badge and the dagger-for-github snippets read from Git tags, groups every update into one PR twice a month (the 1st and the 15th) and refreshes the uv and npm lockfiles once a month, skips the generated code, and never bumps uv_build."
tags: [dependencies, renovate]
generated: { by: claude-code/2.1.310, at: 2026-11-03T10:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: renovate
    resource: https://github.com/telchak/daggerverse/blob/main/renovate.json
    title: "renovate.json"
    author: human:telchak
    last_modified: 2026-10-27T13:30:00Z
  - id: agent-manifest
    resource: https://github.com/telchak/daggerverse/blob/main/angie/dagger-module.toml
    title: "angie/dagger-module.toml (agent manifest)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: claude
    resource: https://github.com/telchak/daggerverse/blob/main/CLAUDE.md
    title: "CLAUDE.md, Working rules"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: label
    resource: https://github.com/telchak/daggerverse/commit/67f7080c002ec91627d14d3b1773d41382d3485e
    title: "fix(renovate): capture full semver in runner label regex"
    author: human:telchak
    last_modified: 2026-04-14T15:45:03+02:00
  - id: tests
    resource: https://github.com/telchak/daggerverse/commit/24a3b0eaf691b0f8e8a8bf1c18e66eea5a90c434
    title: "fix(renovate): include tests/ directory in dagger engine version updates"
    author: human:telchak
    last_modified: 2026-02-28T20:03:42+01:00
---

# Custom managers (`dagger/dagger`, Git tags)

Dagger 1.0 betas are Git tags, not GitHub releases, so every manager reads the `github-tags`
datasource with `semver` versioning, which sees them (`extractVersionTemplate: ^v(?<version>.+)$`).
File patterns use `managerFilePatterns`, which replaces `fileMatch`.[^renovate]

| Where | Regex target |
|-------|--------------|
| `.github/workflows/*.yml` | `DAGGER_VERSION: "<ver>"` |
| `.github/workflows/*.yml` | `runs-on: dagger-v<ver>` (self-hosted runner label; the regex accepts a prerelease suffix such as `-beta.21`) |
| `README.md` files | the static shields badge `label=Dagger&message=v<ver>` (only the root README has one) |
| `README.md` files, Daggie's `system_prompt.md` | `version: "<ver>"` under a `dagger/dagger-for-github@...` step's `with:` (the agents' Actions snippets and Daggie's examples) |

All four land in the same grouped PR (below), so the CLI, the runner label, the badge and the
snippets move together. Until 2026-11-03 they had a group of their own, "dagger engine".[^renovate]

# One PR, twice a month

Every PR push runs CI, and CI's agent tests call Gemini, which [bills per
token](/decisions/gemini-as-ci-llm.md). Since 2026-11-03 Renovate batches its work:[^renovate]

- `group:all` puts every update, majors included (`separateMajorMinor: false`), in one PR,
  `renovate/all`. One failing update fails the whole PR; split it out by hand then.
- `schedule: ["* 0-5 1,15 * *"]`, timezone Europe/Paris: Renovate creates or updates that PR only
  on the 1st and the 15th, between midnight and 6am.
- `updateNotScheduled: false`: outside that window it does not rebase or refresh an existing PR
  either, which would otherwise rerun CI whenever `main` moves.

Before, each dependency got its own PR (ten were open at once in October), and each one ran the
full CI.

# Not managed

- `engineVersion`: the 0.x manager for `dagger.json` was removed. Plain modules have no
  `engineVersion` (static entrypoint), and the agents' `engineVersion = "v1.0.0-0"`[^agent-manifest]
  is written by `dagger generate`, so a Renovate edit would make `dagger check` fail.
- CONTRIBUTING's quoted version and the inline example in Daggie's prompt: bump them by hand on
  the same PR.
- `dagger.lock` (Python SDK and image pins): no custom manager covers it; refresh it with
  `dagger lock update`, then run `dagger generate -y` in case the refresh changed generated code.
- The `examples/` lockfiles: the examples stay on 0.x `dagger.json` without their generated SDK,
  so they cannot be relocked in place (and `ignorePaths` skips them).

# Lockfile maintenance

`lockFileMaintenance` is on, on the 1st of each month between midnight and 6am (weekly on
Mondays until 2026-11-03). Renovate always gives lock file maintenance a branch of its own, even
with a group (its branch-name code separates it from same-group updates), so on the 1st two PRs
open: the grouped one and this one. It refreshes every `uv.lock` (`uv lock
--upgrade` through the pep621 manager) and `package-lock.json` outside the ignored paths.[^renovate]
Before 2026-10-27 nothing refreshed them. Renovate saw only each module's `python >=3.13`
constraint, so the uv lockfiles fell months behind, and 10 locked packages had published
advisories (`urllib3`, `requests`, `certifi`, `protobuf`, `idna`, `anyio`, `pygments`,
`multidict`, `graphql-core`, `opentelemetry-api`). That day they were relocked by hand with the uv
the Python SDK runtime pins in `dagger.lock` (0.13.6). `dagger generate` leaves lockfiles
alone, so a lockfile PR passes `check` without regeneration.

# Rules

- `ignorePaths` adds `*/sdk/**` and `*/clients/**` (generated code) to `examples/`,
  `node_modules`, fixtures and similar paths.[^renovate]
- `dagger-io` and `/^dagger-clients-/` updates are disabled: they are the generated uv workspace
  members, regenerated by `dagger generate`.
- `uv_build` / `uv-build` updates are disabled: the version is dictated by Dagger's Python SDK
  template.
- The Angular fixture's `typescript` is held at `allowedVersions: "<6.1"` (since 2026-10-28).
  Angular 22's `@angular/compiler-cli` and `@angular/build` accept only `>=6.0 <6.1`, and so does
  `22.3.0-next`. TypeScript 7 (PR #74) would break `ng build`. The rule makes Renovate close such
  a PR and stop proposing it. Widen the range in the same change as the first Angular major that
  accepts TypeScript 7. Renovate's Angular major PRs leave the lockfile untouched when the peers
  disagree, so bump `typescript` with them by hand, as on 2026-10-27.

# An engine bump PR

Renovate does not regenerate code: the PR also needs `dagger generate -y`, run with the new CLI
and pushed onto it, before CI's `check` job passes.[^claude] It also needs a self-hosted runner for
the new label; see [upgrade the Dagger engine](/playbooks/upgrade-dagger-engine.md).

# History

The runner-label regex was fixed to capture the full semver on 2026-04-14,[^label] and the
removed `dagger.json` `engineVersion` manager had been extended to `tests/` on 2026-02-28.[^tests]

[^renovate]: renovate.json
[^agent-manifest]: angie/dagger-module.toml (agent manifest)
[^claude]: CLAUDE.md, Working rules
[^label]: fix(renovate): capture full semver in runner label regex
[^tests]: fix(renovate): include tests/ directory in dagger engine version updates
