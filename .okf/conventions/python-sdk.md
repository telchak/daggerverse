---
type: Convention
title: "Python SDK conventions in this repo"
description: "How modules are written with the Dagger Python SDK here: Annotated + Doc on every argument, async functions, dag.* calls, secrets, expect on exec, cache volumes."
tags: [convention, python, dagger]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-03-22T15:43:15+01:00
  - id: angular
    resource: https://github.com/telchak/daggerverse/blob/main/angular/src/angular/main.py
    title: "angular/src/angular/main.py"
    author: human:telchak
    last_modified: 2026-02-22T17:05:17+01:00
  - id: returntype
    resource: https://github.com/telchak/daggerverse/commit/a12ece259f24e8f78bed7b5c3e576af532b59797
    title: "fix: Use dagger.ReturnType.ANY instead of non-existent dagger.ExecExpect.ANY"
    author: human:telchak
    last_modified: 2026-02-17T17:55:01+01:00
  - id: cache
    resource: https://github.com/telchak/daggerverse/commit/19e9520624d9370e423d4547283bf4aad7e47b22
    title: "feat: Add cache volume support to angular, python-build, and gcp-firebase modules"
    author: human:telchak
    last_modified: 2026-02-21T16:38:26+01:00
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Module Guidelines"
    author: human:telchak
    last_modified: 2026-03-05T15:49:35+01:00
  - id: no-await
    resource: https://github.com/telchak/daggerverse/commit/cdb32719847d7f66c78e9956ed8443ecec68c2b7
    title: "fix: remove await from all inter-module gcp_auth calls in tests"
    author: human:telchak
    last_modified: 2026-01-06T19:23:58+01:00
---

# Style

- `@object_type` class per module; `@function` methods; `field()` for constructor fields.
- Every parameter is `Annotated[T, Doc("...")]`; every public function has a docstring. Both
  become CLI help and LLM tool descriptions.[^contributing]
- Names: modules `kebab-case`, functions and params `snake_case` (CLI shows kebab-case).
- Optional objects: `dagger.Directory | None = None`; source dirs use `DefaultPath("/")` on agents.
- Secrets are `dagger.Secret`, mounted with `with_secret_variable`; produce new ones with
  `dag.set_secret(name, value)`. Pass them on the CLI as `env:VAR`.
- Prompt and fixture files are read with `dag.current_module().source().file(...)` (not
  `dag.host()`).

# Exec

- To capture output from failing commands use `with_exec(cmd, expect=...ANY)`. The build modules
  use `dagger.ReturnType.ANY` (2026-02-17, the commit claimed `ExecExpect` did not exist)[^returntype]
  while `_agent_base/workspace.py` and Goose use `dagger.ExecExpect.ANY`. Both are in shipping code
  that passes CI; prefer `ReturnType.ANY` for new code and verify against the SDK before changing either.
- Lazy evaluation: nothing runs until `.stdout()`, `.sync()`, `.contents()` etc.

# Calling other modules

`dag.<module_name>()` (e.g. `dag.gcp_auth()`, `dag.oidc_token()`), generated from `dagger.json`
dependencies. Chained calls that return objects are not awaited; only leaf values are.[^no-await]

# Caching

Optional `npm_cache` / `pip_cache` / `uv_cache` cache-volume parameters (2026-02-21),[^cache]
`dag.cache_volume("node-npm")` for MCP installs. See [cache busting](/conventions/cache-busting.md)
for the opposite problem.

[^returntype]: fix: Use dagger.ReturnType.ANY instead of non-existent dagger.ExecExpect.ANY
[^cache]: feat: Add cache volume support to angular, python-build, and gcp-firebase modules
[^contributing]: Contributing guide, Module Guidelines
[^no-await]: fix: remove await from all inter-module gcp_auth calls in tests
