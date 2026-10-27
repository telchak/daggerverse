---
type: Dagger Module
title: "tests (centralized test module)"
description: "The tests/ Dagger module that exercises every module's public API exactly as a user would: one function per module or agent entrypoint, plus checks wrapping the credential-free tests."
tags: [testing, ci]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/main.py
    title: "tests/src/tests/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/tests/dagger-module.toml
    title: "tests/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml, tests scope"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
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

`tests/` is a plain module with the static entrypoint: `tests/dagger-module.toml` holds
`name = "tests"` and `[entrypoint] kind = "dang"`, `source = "./sdk/entrypoint"`.[^manifest] Its
dependencies are the `clients` of `[sdks.python.scopes.tests]` in the root `dagger.toml`: all 17
modules, agents included (`./angular`, `./angie`, ... `./speck`).[^workspace] `dagger generate`
writes one client per module under `tests/clients/`, committed with `sdk/`; a module missing from
that list has no `dag.<module>()`.

`tests/src/tests/main.py` defines `Tests` with one `@function` per module (`calver`,
`health_check`, `gcp_cloud_run`, ...) and per agent entrypoint (`angie_assist`, `goose_deploy`,
`speck_decompose_with_pr`, ...). Each delegates to a per-module file in `tests/src/tests/`.[^main]
Fixtures live in `tests/src/tests/fixtures/` (`angular-app`, `firestore-scripts`).

The function name **is** the CI contract, unchanged by the 1.0 migration: CI calls
`dagger api call -m ./tests <module>` and `dagger api call -m ./tests <agent>-<suffix>`,[^ci] so a
new module needs a function with its name and a new agent test suffix needs `<agent>_<suffix>`.

Aggregates: `all_no_credentials` (calver, health-check, oidc-token), `all_gcp`, `all_gcp_quick`.

# Checks

Six `@function` + `@check` wrappers run the credential-free tests as checks: `check_calver`,
`check_health_check`, `check_oidc_token`, `check_angular`, `check_python_build` and
`check_dagger_mcp`. A check takes no arguments and returns `None`, so each prints its test's
report and fails when the test raises.[^main] Run them with `dagger check -m ./tests --generated=false`
(without the flag it also runs the slow workspace staleness check): the tests
module is not installed in the workspace, so a plain `dagger check` at the root does not run
them, and neither does CI's `check` job. See [checks](/dagger/checks-and-toolchains.md).

# Conventions

- Output lines are `[OK] ...`, `[!!] ...`, `[--] ...` (some tests still print `PASS: ...`) so CI
  can extract them.
- GCP tests run once per auth method (`AuthMethod.OIDC` "RECOMMENDED", `SERVICE_ACCOUNT`,
  `ACCESS_TOKEN` "LEGACY - NOT RECOMMENDED"), with a UUID cache buster when minting tokens.[^auth]
- Credentials are function parameters, not constructor fields: a constructor approach was
  reverted on 2026-01-01 as an SDK limitation.[^ctor]
- Test sources are cloned at runtime (e.g. RealWorld apps for agents) or bundled as fixtures
  with lockfiles.
- `main.py` is about 1030 lines, over the 600-line limit, which CI only reports as a warning.

Centralized on 2025-12-30[^centralize] and split into per-module files on 2026-01-04.[^split]
See the [decision](/decisions/centralized-tests-module.md) and
[run tests locally](/playbooks/run-tests-locally.md).

[^main]: tests/src/tests/main.py
[^manifest]: tests/dagger-module.toml
[^workspace]: dagger.toml, tests scope
[^ci]: CI workflow
[^auth]: tests/src/tests/auth_utils.py
[^centralize]: refactor: move all test functions to centralized tests module
[^split]: refactor(tests): split into separate files per module
[^ctor]: revert: use function params instead of constructor (SDK limitation)
