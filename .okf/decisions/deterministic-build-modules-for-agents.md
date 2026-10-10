---
type: Decision
title: "Give agents deterministic build modules"
description: "Angular and Python agents call dedicated non-LLM modules (angular, python-build) for build, lint, test, so the reliable path never depends on the model."
tags: [decision, agent, build, deterministic]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
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
    last_modified: 2026-10-01T11:09:06+00:00
---

Added 2026-02-17.[^added] [angular](/modules/angular.md) and [python-build](/modules/python-build.md)
are standalone, published modules; [Angie](/agents/angie.md) and [Monty](/agents/monty.md) depend
on them and expose them as tools (`angular_build`, `python_lint`, ...).[^readme]

The deterministic module can be used directly in CI (or as a toolchain with `@check`), while
the agent uses the same functions when it needs to verify its own work. This is the "deterministic
path first, AI on failure" split; see [AI on failure only](/decisions/ai-on-failure-only.md).

[^added]: feat(angular/python-build): Add deterministic build modules for Angular and Python
[^readme]: Repository README, architecture graph
