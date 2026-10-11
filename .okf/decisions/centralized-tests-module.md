---
type: Decision
title: "Centralize tests in one tests module"
description: "Tests live in tests/ and call modules through their public Dagger API, rather than inside each module."
tags: [decision, testing]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
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
    last_modified: 2026-10-01T11:09:06+00:00
---

Decided on 2025-12-30.[^centralize] "This keeps the main modules clean and tests the public API
exactly as users would."[^readme] Modules ship no test functions, which keeps their published
API minimal, and CI only needs to know `dagger call -m tests <name>`. See
[tests module](/infrastructure/tests-module.md).

[^centralize]: refactor: move all test functions to centralized tests module
[^readme]: Repository README, Testing
