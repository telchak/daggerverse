---
type: Dagger Module
title: "angular"
description: "Deterministic Angular build, lint, test, serve and install functions, plus workspace checks for dagger check; the non-LLM backbone used by the Angie agent."
resource: https://github.com/telchak/daggerverse/tree/main/angular
tags: [module, build, angular, deterministic, checks]
generated: { by: claude-code/2.1.310, at: 2026-10-27T13:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/angular/src/angular/main.py
    title: "angular/src/angular/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/angular/README.md
    title: "angular/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/angular/dagger-module.toml
    title: "angular/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/cc52cbb406cab73785a64debc1aed102d3f7cb35
    title: "feat(angular/python-build): Add deterministic build modules"
    author: human:telchak
    last_modified: 2026-02-17T14:26:23+01:00
  - id: fixture
    resource: https://github.com/telchak/daggerverse/commit/9c93521d9c9871f804e684bb3adf50903fffb76f
    title: "test(angular): use a bundled fixture with a lockfile instead of RealWorld"
    author: claude-code/session
    last_modified: 2026-10-10T14:03:13+00:00
  - id: angular-test
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/angular_module.py
    title: "tests/src/tests/angular_module.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Functions

| Function | Returns |
|----------|---------|
| `build(source, configuration, output_path, node_version="22", npm_cache)` | dist `Directory` |
| `lint(source, fix, node_version, npm_cache)` | output `str` |
| `test(source, watch, browsers, node_version, npm_cache)` | output `str` |
| `serve(source, port, node_version, npm_cache)` | `Service` |
| `install(source, node_version, npm_cache)` | `Directory` with `node_modules` |

Commands run with `expect=dagger.ReturnType.ANY` so lint and test output is returned even on
failure.[^main] `npm_cache` is an optional cache volume (added 2026-02-21, see
[caching](/conventions/cache-busting.md)).

Added on 2026-02-17 together with [python-build](/modules/python-build.md)[^added] so the
agents can call real build tooling; see the
[decision](/decisions/deterministic-build-modules-for-agents.md).

# Workspace checks

Since the Dagger 1.0 migration the module also checks a user's Angular project with no code of
their own: install it in a workspace, then run `dagger check`.[^module-readme]

| Check | Runs |
|-------|------|
| `check-build` | `ng build --configuration production` (through `build`) |
| `check-lint` | `ng lint` (needs `@angular-eslint`) |
| `check-test` | `ng test --watch=false` in `node:<version>-slim`, no browser: suits the Vitest builder, not Karma |

Each check is a `@function` + `@check` that returns `None` and fails on a non-zero exit. It
takes `ws: dagger.Workspace`, which Dagger injects for `dagger check`, and reads
`ws.directory(path, exclude=["node_modules/", "dist/", ".angular/", ".git/"])`. The constructor
args `path="."` and `node_version="22"` are only the checks' settings.[^main]

The workspace is a check argument, not a constructor argument: a module calling another must
pass a Workspace explicitly, so on the constructor it would break the `dag.angular()` calls of
[Angie](/agents/angie.md) and the tests, which keep passing `source` to the functions above. In
1.0, `DefaultPath(".")` of a Git-installed module resolves against the module's own source, so
the workspace is how an installed module reads the user's project. See
[checks](/dagger/checks-and-toolchains.md).

```bash
dagger module install github.com/telchak/daggerverse/angular@<version>
dagger check -l    # list the checks
dagger check       # run them
```

Settings (camelCase keys) and skipped checks go in the user's `dagger.toml`:[^module-readme]

```toml
[modules.angular.settings]
path = "frontend"
nodeVersion = "24"

[modules.angular.check]
skip = ["check-lint"]
```

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed, and a
function signature change needs `dagger generate -y`. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

# Test fixture

Since 2026-10-10 the module test builds a minimal Angular 21 app with a committed
`package-lock.json` at `tests/src/tests/fixtures/angular-app`, because the RealWorld example
only shipped a `bun.lock` and `npm install` against the live registry started crashing.[^fixture]
See the [decision](/decisions/bundled-angular-test-fixture.md). The test also runs `check-build` on
that fixture, passing `source.as_workspace()` explicitly and reading the returned `Check`'s
`pass`.[^angular-test] Run with `dagger check -m ./angular` from the fixture directory on 1.0,
`check-build` passed and `check-lint` / `check-test` failed as expected, since the fixture has
no lint or test target.

[^main]: angular/src/angular/main.py
[^module-readme]: angular/README.md
[^manifest]: angular/dagger-module.toml
[^added]: feat(angular/python-build): Add deterministic build modules
[^fixture]: test(angular): use a bundled fixture with a lockfile instead of RealWorld
[^angular-test]: tests/src/tests/angular_module.py
