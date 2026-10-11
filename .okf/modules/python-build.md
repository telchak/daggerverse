---
type: Dagger Module
title: "python-build"
description: "Deterministic Python build, lint (ruff/flake8/pylint), test, typecheck (mypy/pyright) and install functions; the non-LLM backbone used by Monty."
resource: https://github.com/telchak/daggerverse/tree/main/python-build
tags: [module, build, python, deterministic]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/python-build/src/python_build/main.py
    title: "python-build/src/python_build/main.py"
    author: human:telchak
    last_modified: 2026-02-21T16:38:26+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/python-build/README.md
    title: "python-build/README.md"
    author: human:telchak
    last_modified: 2026-02-21T16:38:26+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/python-build/dagger.json
    title: "python-build/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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
are handled (2026-02-17).[^lockfile] Added alongside [angular](/modules/angular.md), see the
[decision](/decisions/deterministic-build-modules-for-agents.md).

[^main]: python-build/src/python_build/main.py
[^lockfile]: fix: Handle missing lockfile and system Python in build modules
