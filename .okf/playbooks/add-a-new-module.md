---
type: Playbook
title: "Add a new module"
description: "Steps to add a Dagger 1.0 module to this monorepo (scope, generated code, tests) so CI discovers, validates, checks, tests and releases it."
tags: [playbook, module]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Adding a New Module"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (workspace, Python SDK scopes)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

1. From the repository root, `dagger module init python --name <module> --path <module>` and
   `mkdir <module>/examples`. This writes `<module>/dagger-module.toml` and registers the module's
   Python SDK scope in `dagger.toml`.[^contributing]
2. Dependencies are the scope's `clients` in `dagger.toml` (`clients = ["./oidc-token"]`, or a
   pinned Git ref), not the manifest.[^workspace] Run `dagger generate -y`, and again after every
   function signature or client change: the static entrypoint bakes in the module's types.
3. Write the description in `src/<pkg>/__init__.py`'s docstring, starting on the line after
   `"""` (1.0 has no `description` field). See [Daggerverse publishing](/dagger/daggerverse-publishing.md).
4. Implement `src/<pkg>/main.py` following [Python SDK conventions](/conventions/python-sdk.md);
   keep it under 600 lines. A module meant to be installed in a user's workspace reads the project
   through a `ws: dagger.Workspace` argument on its checks, like [angular](/modules/angular.md).
5. Add `README.md` and examples in `examples/{python,go,typescript}` (copy an existing module's;
   examples stay on `dagger.json`).
6. Add `tests/src/tests/<module>.py` and register a `Tests.<module>` function in
   `tests/src/tests/main.py`, plus a `check_<module>` `@check` wrapper (no arguments, returns
   `None`) if it needs no credentials. Add `"./<module>"` to the `clients` of
   `[sdks.python.scopes.tests]` and run `dagger generate -y`. The function name must equal the
   directory name in snake_case: CI calls `dagger api call -m ./tests <module>`.[^ci]
7. GCP module? Name it `gcp-*` so CI injects OIDC args. Other special args need a `case` in `ci.yml`.
8. Commit `dagger.toml`, `dagger.lock`, the generated `sdk/` and `clients/` (of the module and of
   `tests/`) and `uv.lock` (plus lockfiles for example projects, see
   [SonarCloud](/infrastructure/sonarcloud.md)). Check that `dagger check` passes; on a Windows
   host it always fails, see [known issues](/dagger/known-issues-1-0-beta.md).
9. Add it to README tables and the [dependency graph](/overview/dependency-graph.md), and create a
   concept under `.okf/modules/`.
10. Use `feat(<module>): ...`; the first release tags `<module>/v0.1.0`.

[^contributing]: Contributing guide, Adding a New Module
[^workspace]: dagger.toml (workspace, Python SDK scopes)
[^ci]: CI workflow
