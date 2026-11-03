---
type: Reference
title: "Checks, generators and installed modules (0.x toolchains)"
description: "Dagger 1.0 checks, generators, services and installed modules, which replace 0.x toolchains, and how this repository's modules expose them."
tags: [dagger, checks, toolchains, generators, platform-engineering]
generated: { by: claude-code/2.1.310, at: 2026-10-27T13:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: checking
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/using/checking.mdx
    title: "Dagger docs: Checking (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: python
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/sdks/python.mdx
    title: "Dagger docs: Python SDK reference, checks, generators and services (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: wiring
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/config/module-wiring.mdx
    title: "Dagger docs: Module wiring (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: migrate
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/config/migrate-dagger-json.mdx
    title: "Dagger docs: Migrate to Dagger 1.0, toolchains (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: cloud-checks
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/getting-started/cloud-checks.mdx
    title: "Dagger docs: Set up Cloud Checks (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: modfunc
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/modfunc.go
    title: "Dagger engine: workspace argument injection (core/modfunc.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: angular
    resource: https://github.com/telchak/daggerverse/blob/main/angular/src/angular/main.py
    title: "angular/src/angular/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: tests
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/main.py
    title: "tests/src/tests/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Three function kinds

| Kind | Python | Returns | Run by |
|------|--------|---------|--------|
| check | `@function` + `@check` | `None` | `dagger check` |
| generator | `@function` + `@generate` | `dagger.Changeset` | `dagger generate` |
| service | `@function`, no required args | `dagger.Service` | `dagger start` (0.x `dagger up`) |

A check validates and fails by raising (a non-zero exec under `sync()` is enough).[^python]

# dagger check

Runs the checks of every module installed in the workspace, plus one staleness check per
generator (`--generated`, default true: SDK scopes whose committed code differs from
`dagger generate` fail as "generated files are not up to date"). `-l` lists; filters are
`--<module>`, `--check=<name>`, DAG links (`dag://eslint/*`, `dag://**/lint`) and `--skip`;
`--fail-fast`; `-j` parallelism; `-m <module>` loads a one-off module; `--allow-llm`.
Collections add per-item flags (the Go module's `--go-package`, `--go-test`).[^checking]
[Cloud Checks](https://docs.dagger.io/cloud-checks) (`dagger cloud checks on`) run the same
checks on Dagger Cloud engines after each push, without a CI workflow.[^cloud-checks]

# Installed modules replace toolchains

0.x toolchains (`dagger toolchain install`) are gone: `dagger workspace migrate` turns each into
a `[modules.<name>]` entry, with `legacy-default-path = true` to keep resolving its
`defaultPath` arguments against the workspace.[^migrate] In 1.0 an installed module:

- is installed with `dagger module install <ref>` and configured by **settings**, which are its
  constructor arguments (`[modules.angular.settings] nodeVersion = "24"`), possibly wired to
  another module's output (`dag://myapp/serve`);[^wiring]
- reads the user's project through a `dagger.Workspace` argument, which Dagger injects for CLI
  calls, checks, generators and LLM tools. `DefaultPath(".")` of a Git-installed module resolves
  against the module's own source instead.
- cannot keep a Workspace as a field; the docs suggest deriving a Directory in the constructor,[^wiring]
  but a module calling another must pass a Workspace explicitly, and an unset workspace argument,
  even an optional one, fails with "workspace arguments are not inherited by module runtime
  calls".[^modfunc] A module also called by other modules should therefore take the workspace on
  its check functions, not its constructor.

# In this repository

- [angular](/modules/angular.md) and [python-build](/modules/python-build.md) ship workspace
  checks (`check-build`, `check-lint`, `check-test`, and `check-typecheck` for Python). Each takes
  `ws: dagger.Workspace`; the constructor settings `path` and `nodeVersion` / `pythonVersion`
  configure them.[^angular] A user runs `dagger module install
  github.com/telchak/daggerverse/angular@<version>` and then `dagger check`, with no code.
- The [tests module](/infrastructure/tests-module.md) wraps its credential-free tests in
  `check_*` functions, run with `dagger check -m ./tests`.[^tests]
- The root workspace installs only the Python SDK, so `dagger check` at the root runs its
  staleness check. CI runs it in the `check` job ([CI pipeline](/infrastructure/ci-pipeline.md)).
  On Windows this check always fails, see [known issues](/dagger/known-issues-1-0-beta.md).

[^checking]: Dagger docs: Checking (v1.0.0-beta.21)
[^python]: Dagger docs: Python SDK reference, checks, generators and services (v1.0.0-beta.21)
[^wiring]: Dagger docs: Module wiring (v1.0.0-beta.21)
[^migrate]: Dagger docs: Migrate to Dagger 1.0, toolchains (v1.0.0-beta.21)
[^cloud-checks]: Dagger docs: Set up Cloud Checks (v1.0.0-beta.21)
[^modfunc]: Dagger engine: workspace argument injection (core/modfunc.go)
[^angular]: angular/src/angular/main.py
[^tests]: tests/src/tests/main.py
