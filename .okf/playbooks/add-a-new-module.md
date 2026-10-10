---
type: Playbook
title: "Add a new module"
description: "Steps to add a Dagger module to this monorepo so CI discovers, validates, tests and releases it."
tags: [playbook, module]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Adding a New Module"
    author: human:telchak
    last_modified: 2026-03-05T15:49:35+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
---

1. `dagger init --sdk=python --name=<module> <module>/` and create `<module>/examples/`.[^contributing]
2. Set `description` and `engineVersion` (same as the other modules) in `dagger.json`; write the
   real description in `src/<pkg>/__init__.py` (on the line after `"""`). See
   [Daggerverse publishing](/dagger/daggerverse-publishing.md).
3. Implement `src/<pkg>/main.py` following [Python SDK conventions](/conventions/python-sdk.md);
   keep it under 600 lines.
4. Add `README.md` and examples in `examples/{python,go,typescript}` (copy an existing module's).
5. Commit `uv.lock` (and lockfiles for example projects), see [SonarCloud](/infrastructure/sonarcloud.md).
6. Add `tests/src/tests/<module>.py`, register a `Tests.<module>` function in `tests/src/tests/main.py`,
   and add the dependency to `tests/dagger.json` (`../<module>`). The function name must equal the
   directory name in snake_case: CI calls `dagger call -m tests <module>`.[^ci]
7. GCP module? Name it `gcp-*` so CI injects OIDC args. Other special args need a `case` in `ci.yml`.
8. Add it to README tables and the [dependency graph](/overview/dependency-graph.md), and create a
   concept under `.okf/modules/`.
9. Use `feat(<module>): ...`; the first release tags `<module>/v0.1.0`.

[^contributing]: Contributing guide, Adding a New Module
[^ci]: CI workflow
