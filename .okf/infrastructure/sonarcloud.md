---
type: Configuration
title: "SonarCloud quality gate"
description: "SonarCloud's automatic analysis grades every PR; its settings live in the SonarCloud UI (no properties file is read). The generated Dagger 1.0 code must be excluded there, copy-paste detection skips agents, tests and examples, reviewed findings carry NOSONAR, and missing lockfiles lower the security rating."
tags: [quality, sonarcloud]
generated: { by: claude-code/2.1.310, at: 2026-10-27T14:45:00Z }
stale_after: 2027-01-27T00:00:00Z
sources:
  - id: settings
    resource: https://sonarcloud.io/api/settings/values?component=telchak_daggerverse&keys=sonar.exclusions,sonar.cpd.exclusions
    title: "SonarCloud project settings (exclusions), as read on 2026-10-27"
    author: human:telchak
    last_modified: 2026-10-27T14:30:00Z
  - id: autoscan
    resource: https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/automatic-analysis
    title: "SonarQube Cloud docs: Automatic analysis"
    author: team:sonarsource
    last_modified: 2026-10-27T14:30:00Z
  - id: gate
    resource: https://sonarcloud.io/api/qualitygates/project_status?projectKey=telchak_daggerverse&pullRequest=83
    title: "Quality gate of PR #83 (2026-10-27)"
    author: process:sonarcloud
    last_modified: 2026-10-27T14:30:00Z
  - id: locks
    resource: https://github.com/telchak/daggerverse/commit/1a30e63f2f4b75908a98c367eb14447e9c75fde4
    title: "chore(deps): commit missing lockfiles flagged by SonarCloud"
    author: claude-code/session
    last_modified: 2026-10-10T18:54:59+00:00
---

# Where the settings live

The project uses SonarCloud's **automatic analysis**: no scanner runs in CI. That mode ignores
`sonar-project.properties`, and reads `.sonarcloud.properties` only from the default branch,
without wildcards. The settings that apply are therefore the ones in the SonarCloud UI
(Administration > General Settings > Analysis Scope).[^autoscan] As read on 2026-10-27:[^settings]

- `sonar.exclusions`: `angie/src/angie/main.py`, `monty/src/monty/main.py`.
- `sonar.cpd.exclusions` (copy-paste detection): `angie/src/**`, `goose/src/**`, `speck/src/**`,
  `daggie/src/**`, `tests/src/**` and `*/examples/**`. Agents, GCP test scaffolding and example
  modules are intentionally repetitive.

`sonar-project.properties` was deleted on 2026-10-27. It looked like the configuration, but none
of it applied, including the exclusion of the generated code added during the 1.0 migration.

# The generated code must be excluded in the UI

Dagger 1.0 commits generated code in every module: `*/sdk/**` (the vendored Python SDK and the
static entrypoint) and `*/clients/**` (the module clients, a copy of the core client in each).
Unless the UI excludes `**/sdk/**` and `**/clients/**` (and `.claude/**`, the vendored okf-skills
tooling), SonarCloud reads them as project code. On PR #83 that came to about 520,000 duplicated
lines of 530,000 new ones: a 98% duplication density against the gate's 3%.[^gate] PR #82 failed
the same way.

# Gate conditions on new code

- Duplicated lines at most 3%.
- Security rating A. A single vulnerability lowers it. On PR #83 there were five: four
  `python:S5443` ("publicly writable directory") on `/tmp` paths, and one `githubactions:S7637`
  ("use full commit SHA") on `dagger/dagger-for-github@v8.4.1`.[^gate]
  - The `/tmp` lines are the token files of `gcp-auth`, `gcp-artifact-registry` and
    `oidc-token`, and `_agent_base`'s MCP driver. Each runs in a single-use container that
    nothing else shares, and `/tmp` stays writable whatever user an image runs as. They carry
    `# NOSONAR`, with the reason on the line above: the only NOSONARs in the repo.
  - The action is now pinned to its commit SHA, with a `# v8.4.1` comment that Renovate keeps in
    step.

# Lockfiles

SonarCloud rates Security C when a `pyproject.toml` or `package.json` has no lockfile next to it
("Dependency versions are not predictable"). On 2026-10-10 every missing `uv.lock`, `yarn.lock`
and `package-lock.json` was committed.[^locks] On 1.0 the generated `sdk/` and `clients/` are
committed uv workspace members, and `uv.lock` is committed with them after `dagger generate -y`.
**Commit a lockfile with any new `pyproject.toml` or `package.json`.**

Many commits titled "Fix Sonarqube issues" (2026-02) reshaped code for the gate: unused params,
dict literals, async misuse, top-level await.

[^settings]: SonarCloud project settings (exclusions), as read on 2026-10-27
[^autoscan]: SonarQube Cloud docs: Automatic analysis
[^gate]: Quality gate of PR #83 (2026-10-27)
[^locks]: chore(deps): commit missing lockfiles flagged by SonarCloud
