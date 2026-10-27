---
type: Reference
title: "Dagger modules, dependencies and the Daggerverse install path"
description: "How Dagger 1.0 modules declare dependencies (scope clients), are installed and referenced by version, and reach the user's project (Workspace, DefaultPath), as used in this repo."
tags: [dagger, modules, dependencies, workspace]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: python
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/sdks/python.mdx
    title: "Dagger docs: Python SDK reference, module dependencies and workspace inputs (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: toml
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/config-files/dagger-toml.mdx
    title: "Dagger docs: dagger.toml reference (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: migrate
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/config/migrate-dagger-json.mdx
    title: "Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: git-go
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/core/git.go
    title: "Dagger engine: version tag selection (core/git.go, SelectGitRefWithVersionQuery)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: agents-design
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/hack/designs/workspace-agents.md
    title: "Dagger design: Workspace Agents, workspace propagation (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: workspace-toml
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (this repository)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Manifest and generated code

`dagger-module.toml` names the module and its entrypoint or runtime; generated code (`sdk/`,
`clients/`) is committed. Details in [workspaces](/dagger/dagger-1-0-workspaces.md). `include`
(extra paths uploaded with the module, how [agent-base](/agents/agent-base.md) ships) is only
valid on a runtime manifest.

# Dependencies are scope clients

A Python module's dependencies are the `clients` of its scope in `dagger.toml`: local paths
relative to the directory holding `dagger.toml` (`./oidc-token`; a bare `oidc-token` is not a
path) or Git refs.[^toml] From the module directory:[^python]

```shell
dagger module client add github.com/kpenfound/dag/github-issue@<ref> --sdk=python
dagger module client list --sdk=python
dagger module client update --sdk=python   # refreshes dagger.lock
dagger module client rm <ref> --sdk=python
```

Each command updates `dagger.toml` and regenerates the module: one `clients/<dependency>` package
per client, exposed as `dag.<dependency>()` (this repo sets `global-client = true`) or imported
from `dagger_clients.<dependency>`. In this repo every client is edited in the root
`dagger.toml`, followed by `dagger generate -y`.[^workspace-toml]

# Using a published module

- Into a workspace (zero code, checks and functions available):
  `dagger module install github.com/telchak/daggerverse/calver@<version>` (`dagger install` is the
  same), recorded as `[modules.calver]`.
- As a dependency of a module: `dagger module client add github.com/telchak/daggerverse/calver@<version> --sdk=python`.
- One-off: `dagger api call -m github.com/telchak/daggerverse/goose@<version> troubleshoot ...`;
  locally `dagger api call -m ./goose ...`.
- **Versions:** a version query first matches tags under the module's subpath, so in this
  monorepo `@v1.0.0` resolves `calver/v1.0.0`, and `@v1.0` the greatest matching `calver/v1.0.*`;
  then repository-wide tags, then branches. No version selects the latest stable `calver/v*` tag,
  falling back to HEAD.[^git-go] `@calver/v1.0.0` (the full tag) always works.

# Reaching the user's project

- Since v0.20 modules cannot read the host (`dag.host()` removed): files arrive as `Directory` or
  `File` arguments, or through a `dagger.Workspace` argument.
- A `Workspace` argument is injected for CLI calls, checks, generators and LLM tools; it is lazy
  (`ws.directory(path, exclude=..., include=..., gitignore=...)`, `ws.file`, `ws.find_up`;
  relative paths from the workspace cwd, `/` from its root) and cannot be stored as a field.[^python]
- It does not cross module boundaries: a module function calling another module must pass a
  Workspace explicitly, otherwise the call fails.[^agents-design]
- `DefaultPath` still works, but for a module installed from Git it resolves against the
  module's own source; `legacy-default-path = true` on a migrated toolchain keeps the 0.x
  behaviour of resolving it against the workspace.[^migrate]

[^python]: Dagger docs: Python SDK reference, module dependencies and workspace inputs (v1.0.0-beta.21)
[^toml]: Dagger docs: dagger.toml reference (v1.0.0-beta.21)
[^migrate]: Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)
[^git-go]: Dagger engine: version tag selection (core/git.go, SelectGitRefWithVersionQuery)
[^agents-design]: Dagger design: Workspace Agents, workspace propagation (v1.0.0-beta.21)
[^workspace-toml]: dagger.toml (this repository)
