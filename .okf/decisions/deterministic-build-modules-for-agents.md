---
type: Decision
title: "Give agents deterministic build modules"
description: "Angular and Python agents call dedicated non-LLM modules (angular, python-build) for build, lint, test, so the reliable path never depends on the model."
tags: [decision, agent, build, deterministic]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/cc52cbb406cab73785a64debc1aed102d3f7cb35
    title: "feat(angular/python-build): Add deterministic build modules for Angular and Python"
    author: human:telchak
    last_modified: 2026-02-17T14:26:23+01:00
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, architecture graph"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: angular-main
    resource: https://github.com/telchak/daggerverse/blob/main/angular/src/angular/main.py
    title: "angular/src/angular/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: angie-main
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

Added 2026-02-17.[^added] [angular](/modules/angular.md) and [python-build](/modules/python-build.md)
are standalone, published modules; [Angie](/agents/angie.md) and [Monty](/agents/monty.md) depend
on them and expose them as tools (`angular_build`, `python_lint`, ...).[^readme]

The deterministic module can be used directly in CI (or as a toolchain with `@check`), while
the agent uses the same functions when it needs to verify its own work. This is the "deterministic
path first, AI on failure" split; see [AI on failure only](/decisions/ai-on-failure-only.md).

# Dagger 1.0 consequence

Toolchains are gone in 1.0, so the "toolchain with `@check`" path became workspace checks: both
modules ship `check-build`, `check-lint` and `check-test` (plus `check-typecheck` for Python),
which a user gets with `dagger module install` and `dagger check`. Each check takes the workspace
as an argument, not on the constructor,[^angular-main] so the agents' tools keep calling the same
Directory functions, e.g. `dag.angular().build(source=ws.directory("."), ...)`.[^angie-main] See
[checks](/dagger/checks-and-toolchains.md).

[^added]: feat(angular/python-build): Add deterministic build modules for Angular and Python
[^readme]: Repository README, architecture graph
[^angular-main]: angular/src/angular/main.py
[^angie-main]: angie/src/angie/main.py
