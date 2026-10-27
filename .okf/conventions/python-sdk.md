---
type: Convention
title: "Python SDK conventions in this repo"
description: "How modules are written with the Dagger Python SDK here: Annotated + Doc on every argument, async functions, dag.* calls through generated clients, workspace arguments and checks, secrets, ReturnType.ANY on exec, cache volumes."
tags: [convention, python, dagger]
generated: { by: claude-code/2.1.310, at: 2026-10-27T09:30:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: gcp-auth
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/src/gcp_auth/main.py
    title: "gcp-auth/src/gcp_auth/main.py"
    author: human:telchak
    last_modified: 2026-10-27T09:30:00Z
  - id: exec-go
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/container_exec.go
    title: "Dagger engine: withExec options (core/container_exec.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: angie
    resource: https://github.com/telchak/daggerverse/blob/main/angie/src/angie/main.py
    title: "angie/src/angie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: angular
    resource: https://github.com/telchak/daggerverse/blob/main/angular/src/angular/main.py
    title: "angular/src/angular/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace-py
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/workspace.py
    title: "_agent_base/src/agent_base/workspace.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: returntype
    resource: https://github.com/telchak/daggerverse/commit/a12ece259f24e8f78bed7b5c3e576af532b59797
    title: "fix: Use dagger.ReturnType.ANY instead of non-existent dagger.ExecExpect.ANY"
    author: human:telchak
    last_modified: 2026-02-17T17:55:01+01:00
  - id: scope
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml, Python SDK scopes and clients"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: pyproject
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/pyproject.toml
    title: "gcp-auth/pyproject.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: modfunc
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/modfunc.go
    title: "Dagger engine: workspace argument injection (core/modfunc.go)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: wiring
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/config/module-wiring.mdx
    title: "Dagger docs: Module wiring (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: python
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/sdks/python.mdx
    title: "Dagger docs: Python SDK reference (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: cache
    resource: https://github.com/telchak/daggerverse/commit/19e9520624d9370e423d4547283bf4aad7e47b22
    title: "feat: Add cache volume support to angular, python-build, and gcp-firebase modules"
    author: human:telchak
    last_modified: 2026-02-21T16:38:26+01:00
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Module Guidelines"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: no-await
    resource: https://github.com/telchak/daggerverse/commit/cdb32719847d7f66c78e9956ed8443ecec68c2b7
    title: "fix: remove await from all inter-module gcp_auth calls in tests"
    author: human:telchak
    last_modified: 2026-01-06T19:23:58+01:00
---

# Style

- `@object_type` class per module; `@function` methods; `field()` exposes a constructor field
  through the API, while a plain annotated attribute is private state, still a constructor
  argument[^python] (the angular and python-build check settings).[^angular]
- Every parameter is `Annotated[T, Doc("...")]`; every public function has a docstring. Both
  become CLI help and LLM tool descriptions.[^contributing]
- Names: modules `kebab-case`, functions and params `snake_case` (CLI shows kebab-case).
- Optional objects: `dagger.Directory | None = None`; source dirs use `DefaultPath("/")` on agents.
- Secrets are `dagger.Secret`, mounted with `with_secret_variable`; produce new ones with
  `dag.set_secret(name, value)`. Pass them on the CLI as `env:VAR`.
- Prompt and fixture files are read with `dag.current_module().source().file(...)` (not
  `dag.host()`).

# Exec

- To capture output from failing commands use `with_exec(cmd, expect=dagger.ReturnType.ANY)`;
  all code does (`angular`, `python-build`, and `_agent_base/workspace.py`, which Goose's grep now
  uses too).[^angular][^workspace-py] The 1.0 core client only has `ReturnType`:
  `dagger.ExecExpect.ANY`, which `_agent_base/workspace.py` and Goose used on 0.x, never existed,
  as the 2026-02-17 commit that switched the build modules said.[^returntype]
- Lazy evaluation: nothing runs until `.stdout()`, `.sync()`, `.contents()` etc.
- A credential is never an exec's stdout. Dagger logs every exec's stdout: CI's `plain` progress
  prints it into this repository's public logs, and traces keep it. GitHub masks the secrets it
  knows about, not a token minted from them. Write the value to a file in the container
  (`sh -c "gcloud auth print-access-token > /tmp/access-token"`), read it with
  `.file(path).contents()`, then wrap it with `dag.set_secret()`.[^gcp-auth] `redirect_stdout` is
  no substitute: the engine still logs redirected streams for callers on API views before
  v1.0.0.[^exec-go] gcp-auth, gcp-artifact-registry, oidc-token and the tests printed tokens until
  2026-10-27. SonarCloud flags such `/tmp` paths (`python:S5443`). In a single-use container
  nothing else shares `/tmp`, and it is writable whatever user the image runs as, so the flagged
  line carries `# NOSONAR` with the reason on the line above; see
  [SonarCloud](/infrastructure/sonarcloud.md).

# Calling other modules

`dag.<module_name>()` (e.g. `dag.gcp_auth()`, `dag.oidc_token()`) comes from the scope's generated
clients: each entry of the module's `clients` in the root `dagger.toml` (`["./oidc-token"]` for
gcp-auth)[^scope] becomes `clients/<dep>`, a `dagger-clients-<dep>` uv workspace member, and
`[tool.dagger] global-client = true` in `pyproject.toml` keeps `from dagger import dag`
working.[^pyproject] Add the client, then run `dagger generate -y`. Chained calls that return
objects are not awaited; only leaf values are.[^no-await]

# Workspace arguments and checks

- A `ws: dagger.Workspace` argument is injected for calls from outside a module (CLI,
  `dagger check`, `dagger generate`) and for LLM tool calls (the LLM's bound workspace). It is not
  injected for module-to-module calls: the caller must pass one, and an unset workspace argument,
  even an optional one, fails with "workspace arguments are not inherited by module runtime
  calls".[^modfunc]
- A module object cannot keep a Workspace as a field; the docs derive a Directory from it in the
  constructor.[^wiring] Modules that other modules call (angular, python-build) take `ws` on their
  check functions instead and read the project with `ws.directory(self.path, exclude=[...])`,
  keeping only settings such as `path` and `node_version` on the constructor.[^angular]
- `DefaultPath` of a Git-installed module resolves against the module's own source, so an
  installed module reads the user's project through its workspace argument. The Directory
  functions with `DefaultPath(".")` (`build`, `lint`, ...) are unchanged; callers pass `source`,
  e.g. Angie's `dag.angular().install(source=ws.directory("."))`.[^angie]
- A check is `@function` + `@check` (`from dagger import check`), returns `None` and fails by
  raising; run the container with `.sync()` and a non-zero exit fails it.[^python]

See [checks and installed modules](/dagger/checks-and-toolchains.md).

# Caching

Optional `npm_cache` / `pip_cache` / `uv_cache` cache-volume parameters (2026-02-21),[^cache]
`dag.cache_volume("node-npm")` for MCP installs. See [cache busting](/conventions/cache-busting.md)
for the opposite problem.

[^angie]: angie/src/angie/main.py
[^angular]: angular/src/angular/main.py
[^workspace-py]: _agent_base/src/agent_base/workspace.py
[^returntype]: fix: Use dagger.ReturnType.ANY instead of non-existent dagger.ExecExpect.ANY
[^scope]: dagger.toml, Python SDK scopes and clients
[^pyproject]: gcp-auth/pyproject.toml
[^modfunc]: Dagger engine: workspace argument injection (core/modfunc.go)
[^wiring]: Dagger docs: Module wiring (v1.0.0-beta.21)
[^python]: Dagger docs: Python SDK reference (v1.0.0-beta.21)
[^cache]: feat: Add cache volume support to angular, python-build, and gcp-firebase modules
[^contributing]: Contributing guide, Module Guidelines
[^no-await]: fix: remove await from all inter-module gcp_auth calls in tests
[^gcp-auth]: gcp-auth/src/gcp_auth/main.py
[^exec-go]: Dagger engine: withExec options (core/container_exec.go)
