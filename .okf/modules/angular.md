---
type: Dagger Module
title: "angular"
description: "Deterministic Angular build, lint, test, serve and install functions; the non-LLM backbone used by the Angie agent."
resource: https://github.com/telchak/daggerverse/tree/main/angular
tags: [module, build, angular, deterministic]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/angular/src/angular/main.py
    title: "angular/src/angular/main.py"
    author: human:telchak
    last_modified: 2026-02-22T17:05:17+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/angular/README.md
    title: "angular/README.md"
    author: human:telchak
    last_modified: 2026-02-21T16:38:26+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/angular/dagger.json
    title: "angular/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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

# Test fixture

Since 2026-10-10 the module test builds a minimal Angular 21 app with a committed
`package-lock.json` at `tests/src/tests/fixtures/angular-app`, because the RealWorld example
only shipped a `bun.lock` and `npm install` against the live registry started crashing.[^fixture]
See the [decision](/decisions/bundled-angular-test-fixture.md).

[^main]: angular/src/angular/main.py
[^added]: feat(angular/python-build): Add deterministic build modules
[^fixture]: test(angular): use a bundled fixture with a lockfile instead of RealWorld
