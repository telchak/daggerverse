---
type: Configuration
title: "SonarCloud quality gate"
description: "SonarCloud analyses the repo (Python 3.13) without the vendored tooling and the generated Dagger 1.0 code (sdk/, clients/); copy-paste detection is disabled for agents, tests and examples, and missing lockfiles lower the security rating."
tags: [quality, sonarcloud]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: props
    resource: https://github.com/telchak/daggerverse/blob/main/sonar-project.properties
    title: "sonar-project.properties"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: locks
    resource: https://github.com/telchak/daggerverse/commit/1a30e63f2f4b75908a98c367eb14447e9c75fde4
    title: "chore(deps): commit missing lockfiles flagged by SonarCloud"
    author: claude-code/session
    last_modified: 2026-10-10T18:54:59+00:00
---

`sonar-project.properties` sets `sonar.python.version=3.13` and:[^props]

- `sonar.exclusions=.claude/**,*/sdk/**,*/clients/**`: code that is not the project's. `.claude/**`
  is the vendored okf-skills tooling; `*/sdk/**` (the vendored Python SDK and the static
  entrypoint) and `*/clients/**` (the module clients) are the Dagger 1.0 generated code committed
  in every module.
- `sonar.cpd.exclusions` (copy-paste detection) for `monty/src`, `angie/src`, `goose/src`,
  `speck/src`, `daggie/src`, `tests/src` and `*/examples`, because agents, GCP test scaffolding
  and example modules are intentionally repetitive.

SonarCloud rates Security C when a `pyproject.toml` or `package.json` has no lockfile next to it
("Dependency versions are not predictable"). On 2026-10-10 every missing `uv.lock`,
`yarn.lock` and `package-lock.json` was committed; the module locks were then generated with
`uv lock` against a stub of the generated `sdk/` package, which 0.x did not commit.[^locks] On 1.0
the generated `sdk/` and `clients/` are committed uv workspace members, and `uv.lock` is
committed with them after `dagger generate -y`. **Commit a lockfile with any new
`pyproject.toml` or `package.json`.**

Many commits titled "Fix Sonarqube issues" (2026-02) reshaped code for the gate: unused params,
dict literals, async misuse, top-level await.

[^props]: sonar-project.properties
[^locks]: chore(deps): commit missing lockfiles flagged by SonarCloud
