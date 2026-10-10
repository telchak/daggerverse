---
type: Dagger Module
title: "tests (centralized test module)"
description: "The tests/ Dagger module that exercises every module's public API exactly as a user would, one function per module or agent entrypoint."
tags: [testing, ci]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/main.py
    title: "tests/src/tests/main.py"
    author: human:telchak
    last_modified: 2026-10-10T14:03:13+00:00
  - id: auth
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/auth_utils.py
    title: "tests/src/tests/auth_utils.py"
    author: human:telchak
    last_modified: 2026-02-12T18:58:50+01:00
  - id: centralize
    resource: https://github.com/telchak/daggerverse/commit/41c0fb3a83e23636de7d046e3db4b5252eb71046
    title: "refactor: move all test functions to centralized tests module"
    author: human:telchak
    last_modified: 2025-12-30T18:21:03+01:00
  - id: split
    resource: https://github.com/telchak/daggerverse/commit/6f0138fdbcd6730d803683cc06181963735fdcdc
    title: "refactor(tests): split into separate files per module"
    author: human:telchak
    last_modified: 2026-01-04T23:22:21+01:00
  - id: ctor
    resource: https://github.com/telchak/daggerverse/commit/7343c56243495e8adc6271f013c5b73faeedb997
    title: "revert: use function params instead of constructor (SDK limitation)"
    author: human:telchak
    last_modified: 2026-01-01T19:27:06+01:00
---

# Layout

`tests/src/tests/main.py` defines `Tests` with one `@function` per module (`calver`,
`health_check`, `gcp_cloud_run`, ...) and per agent entrypoint (`angie_assist`, `goose_deploy`,
`speck_decompose_with_pr`, ...). Each delegates to `tests/src/tests/<module>.py`.[^main]
Fixtures live in `tests/src/tests/fixtures/` (`angular-app`, `firestore-scripts`).

The function name **is** the CI contract: CI calls `dagger call -m tests <module>` and
`dagger call -m tests <agent>-<suffix>`, so a new module needs a function with its name and a
new agent test suffix needs `<agent>_<suffix>`.

Aggregates: `all_no_credentials` (calver, health-check, oidc-token, semver),
`all_gcp`, `all_gcp_quick`.

# Conventions

- Output lines are `[OK] ...`, `[!!] ...`, `[--] ...` so CI can extract them.
- GCP tests run once per auth method (`AuthMethod.OIDC` "RECOMMENDED", `SERVICE_ACCOUNT`,
  `ACCESS_TOKEN` "LEGACY - NOT RECOMMENDED"), with a UUID cache buster when minting tokens.[^auth]
- Credentials are function parameters, not constructor fields: a constructor approach was
  reverted on 2026-01-01 as an SDK limitation.[^ctor]
- Test sources are cloned at runtime (e.g. RealWorld apps for agents) or bundled as fixtures
  with lockfiles.

Centralized on 2025-12-30[^centralize] and split into per-module files on 2026-01-04.[^split]
See the [decision](/decisions/centralized-tests-module.md) and
[run tests locally](/playbooks/run-tests-locally.md).

[^main]: tests/src/tests/main.py
[^auth]: tests/src/tests/auth_utils.py
[^centralize]: refactor: move all test functions to centralized tests module
[^split]: refactor(tests): split into separate files per module
[^ctor]: revert: use function params instead of constructor (SDK limitation)
