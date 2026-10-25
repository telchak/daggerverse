---
type: Reference
title: "Dagger 1.0 workspaces (dagger.toml, dagger.lock, dagger-module.toml)"
description: "How Dagger 1.0 splits dagger.json into a workspace config, a lockfile and a module manifest, and how this repository uses them."
tags: [dagger, workspace, migration, configuration]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: migrate
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/config/migrate-dagger-json.mdx
    title: "Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: toml
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/config-files/dagger-toml.mdx
    title: "Dagger docs: dagger.toml reference (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: python
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/sdks/python.mdx
    title: "Dagger docs: Python SDK reference (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: python-sdk
    resource: https://github.com/dagger/python-sdk/blob/v1.2.0/README.md
    title: "dagger/python-sdk README (v1.2.0)"
    author: team:dagger
  - id: workspace-toml
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (this repository)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: lock
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.lock
    title: "dagger.lock (this repository)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

Dagger 1.0 is in beta (`v1.0.0-beta.1` to `beta.21` are Git tags, not GitHub releases); this
repository runs on **1.0.0-beta.21**. In 0.x, `dagger.json` was both a module manifest and a
workspace configuration. 1.0 splits it:[^migrate]

| Role | 0.x | 1.0 |
|------|-----|-----|
| module manifest | `dagger.json` | `dagger-module.toml` |
| workspace configuration | `dagger.json` | `dagger.toml` |
| pinned images, Git refs, vanity URLs | none | `dagger.lock` |

1.0 still loads `dagger.json` (it prints "No workspace config found, inferring from
dagger.json"), so a project can migrate step by step.[^migrate]

# dagger.toml

The nearest `dagger.toml` above the current directory configures the workspace. Keys:[^toml]

- `[modules.<name>]`: installed modules (`source`, `pin`, `settings` = constructor arguments with
  camelCase keys, `main`, and `check.skip` / `generate.skip` / `up.skip` lists of kebab-case
  function names). A setting can be a `dag://<module>/<function>` reference to another module's
  output.
- `[sdks.<sdk>]`: the installed module that provides an SDK and its **scopes**, keyed by path.
  A scope has `is-module`, `clients` (dependencies: `./path` or a Git ref) and `settings`.
- `[env.<name>]` overlays, `[[include]]` (inherit another config), `ignore`, `check-generated`
  (default true: `dagger check` also runs the generators' staleness checks).

Unknown fields are an error.

# dagger.lock

Pins the images and Git refs the workspace resolves. Any Dagger command may add entries; commit
it. `dagger lock update [selector...]` refreshes, `dagger lock list` shows entries. A remote
workspace (`dagger check -W github.com/org/repo@main`, Cloud Checks) uses the committed lock and
never writes it.[^toml]

# dagger-module.toml and generated code

A migrated module "does not run SDK codegen at runtime": it fails to load until `dagger generate`
has written its generated code, which is committed.[^migrate] For the Python SDK
(`github.com/dagger/python-sdk`) that is `sdk/` (the vendored `dagger-io` library), `clients/core`
and one `clients/<dependency>` per client, all uv workspace members.[^python-sdk] Two manifest
shapes exist:

| Shape | Manifest | Used here by |
|-------|----------|--------------|
| static entrypoint | `name` + `[entrypoint] kind = "dang"`, `source = "./sdk/entrypoint"`: generated Dang code with the module's types baked in; no `engineVersion`, runs on the engine's version | the 12 plain modules and `tests` |
| runtime | `name`, `engineVersion`, `include`, `[runtime] source = "dagger.io/sdk/python/runtime@v1"`: the module is built and introspected at load time | the 5 agents (`legacyRuntime = true` scope setting) |

There is no `description` field; the Daggerverse description is the package docstring. Re-run
`dagger generate -y` after changing a function signature, a scope's clients or the Dagger
version.[^python]

# Migration commands

- `dagger workspace migrate [-y|--no-apply]` migrates a workspace whose root holds `dagger.json`
  (toolchains become installed modules, `legacy-default-path = true` keeps their 0.x
  `defaultPath` behaviour; writes `.dagger/migration-report.md`).
- `dagger module migrate <path> -y` migrates one module. Coding agents must pass `-y` or
  `--no-apply`.[^migrate]
- Python modules must be migrated and generated in dependency order: a dependent fails with
  "generated file sdk/pyproject.toml is missing" until its dependencies are generated.[^python-sdk]

# In this repository

The root has no module, so each module was migrated with `dagger module migrate` (the `tests`
module by hand, see [known issues](/dagger/known-issues-1-0-beta.md)). The root
`dagger.toml`[^workspace-toml] installs the Python SDK and declares one scope per module, whose
`clients` are its dependencies (`./oidc-token` for `gcp-auth`, all 17 modules for `tests`, the
build modules and `github-issue` for the agents). `dagger.lock`[^lock] pins the Python SDK
(v1.2.0) and the images the modules and tests pull. The `examples/` modules stay on `dagger.json`.
See the [migration decision](/decisions/migrate-to-dagger-1-0.md),
[module system](/dagger/module-system.md) and [module anatomy](/conventions/module-anatomy.md).

[^migrate]: Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)
[^toml]: Dagger docs: dagger.toml reference (v1.0.0-beta.21)
[^python]: Dagger docs: Python SDK reference (v1.0.0-beta.21)
[^python-sdk]: dagger/python-sdk README (v1.2.0)
[^workspace-toml]: dagger.toml (this repository)
[^lock]: dagger.lock (this repository)
