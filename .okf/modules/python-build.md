---
type: Dagger Module
title: "python-build"
description: "Deterministic Python build, lint (ruff/flake8/pylint), test, typecheck (mypy/pyright) and install functions, plus workspace checks for dagger check; the non-LLM backbone used by Monty."
resource: https://github.com/telchak/daggerverse/tree/main/python-build
tags: [module, build, python, deterministic, checks]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/python-build/src/python_build/main.py
    title: "python-build/src/python_build/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/python-build/README.md
    title: "python-build/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/python-build/dagger-module.toml
    title: "python-build/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/cc52cbb406cab73785a64debc1aed102d3f7cb35
    title: "feat(angular/python-build): Add deterministic build modules"
    author: human:telchak
    last_modified: 2026-02-17T14:26:23+01:00
  - id: lockfile
    resource: https://github.com/telchak/daggerverse/commit/b406eb5a6c87c469f814d0e1143f716cc15415cd
    title: "fix: Handle missing lockfile and system Python in build modules"
    author: human:telchak
    last_modified: 2026-02-17T19:50:11+01:00
---

# Functions

| Function | Defaults |
|----------|----------|
| `build(source, command="", python_version="3.13", pip_cache, uv_cache)` | auto-detects the build command when empty |
| `lint(source, tool="ruff", fix, ...)` | `ruff`, `flake8` or `pylint` |
| `test(source, command="", ...)` | auto-detects when empty |
| `typecheck(source, tool="mypy", ...)` | `mypy` or `pyright` |
| `install(source, ...)` | returns the source with dependencies installed |

Commands run with `expect=dagger.ReturnType.ANY`.[^main] Missing lockfiles and system Python
are handled (2026-02-17).[^lockfile] Added alongside [angular](/modules/angular.md),[^added] see the
[decision](/decisions/deterministic-build-modules-for-agents.md).

# Workspace checks

Since the Dagger 1.0 migration the module also checks a user's Python project with no code of
their own: install it in a workspace, then run `dagger check`.[^module-readme]

| Check | Runs |
|-------|------|
| `check-lint` | `ruff check .` |
| `check-test` | `python -m pytest` (installed if missing), after installing the project's dependencies |
| `check-typecheck` | `python -m mypy .`, after installing the project's dependencies |
| `check-build` | `python -m build` (through `build`) |

Each check is a `@function` + `@check` that returns `None` and fails on a non-zero exit. It
takes `ws: dagger.Workspace`, which Dagger injects for `dagger check`, and reads
`ws.directory(path, exclude=[...])`, leaving out `.venv/`, `**/__pycache__/`, `.git/`, `dist/`,
`build/` and the mypy, pytest and ruff caches. The constructor args `path="."` and
`python_version="3.13"` are only the checks' settings.[^main]

The workspace is a check argument, not a constructor argument: a module calling another must
pass a Workspace explicitly, so on the constructor it would break the `dag.python_build()` calls
of [Monty](/agents/monty.md) and the tests, which keep passing `source` to the functions above.
In 1.0, `DefaultPath(".")` of a Git-installed module resolves against the module's own source, so
the workspace is how an installed module reads the user's project. See
[checks](/dagger/checks-and-toolchains.md).

```bash
dagger module install github.com/telchak/daggerverse/python-build@<version>
dagger check -l    # list the checks
dagger check       # run them
```

Settings (camelCase keys) and skipped checks go in the user's `dagger.toml`:[^module-readme]

```toml
[modules.python-build.settings]
path = "backend"
pythonVersion = "3.12"

[modules.python-build.check]
skip = ["check-typecheck"]
```

Run with `dagger check -m ./python-build` from a small Git-tracked Python project on 1.0 (Windows
host), `check-test`, `check-typecheck` and `check-build` passed, and `check-lint` failed only on
ruff `EXE002`, caused by the Windows upload modes (see
[known issues](/dagger/known-issues-1-0-beta.md)). No CI test covers these checks yet.

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed, and a
function signature change needs `dagger generate -y`. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: python-build/src/python_build/main.py
[^module-readme]: python-build/README.md
[^manifest]: python-build/dagger-module.toml
[^added]: feat(angular/python-build): Add deterministic build modules
[^lockfile]: fix: Handle missing lockfile and system Python in build modules
