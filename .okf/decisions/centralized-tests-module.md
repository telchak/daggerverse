---
type: Decision
title: "Centralize tests in one tests module"
description: "Tests live in tests/ and call modules through their public Dagger API, rather than inside each module."
tags: [decision, testing]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: centralize
    resource: https://github.com/telchak/daggerverse/commit/41c0fb3a83e23636de7d046e3db4b5252eb71046
    title: "refactor: move all test functions to centralized tests module"
    author: human:telchak
    last_modified: 2025-12-30T18:21:03+01:00
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Testing"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, test jobs"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (workspace), tests scope"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: tests-main
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/main.py
    title: "tests/src/tests/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

Decided on 2025-12-30.[^centralize] "This keeps the main modules clean and tests the public API
exactly as users would."[^readme] Modules ship no test functions, which keeps their published
API minimal, and CI only needs to know one call shape: `dagger call -m tests <name>` in 0.x,
`dagger api call -m ./tests <name>` since the Dagger 1.0 migration.[^ci] See
[tests module](/infrastructure/tests-module.md).

# Dagger 1.0 consequence

The decision holds; only the wiring changed. The tests module reaches every module as a client:
its scope in the root `dagger.toml` lists all 17 (`./angular` ... `./speck`).[^workspace] Its
credential-free tests are also wrapped as `check_*` functions run with `dagger check -m ./tests`;
the tests module is not installed in the workspace, so a root `dagger check` does not run
them.[^tests-main]

[^centralize]: refactor: move all test functions to centralized tests module
[^readme]: Repository README, Testing
[^ci]: CI workflow, test jobs
[^workspace]: dagger.toml (workspace), tests scope
[^tests-main]: tests/src/tests/main.py
