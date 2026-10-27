# Dagger platform

Upstream Dagger knowledge this repo depends on, pinned to v1.0.0-beta.21.

* [Dagger releases and breaking changes relevant here](breaking-changes.md) - Engine changes from v0.19 to v1.0.0-beta.21 that affected or constrain this repository's modules, including the 0.x to 1.0 migration.
* [Checks, generators and installed modules (0.x toolchains)](checks-and-toolchains.md) - Dagger 1.0 checks, generators, services and installed modules, which replace 0.x toolchains, and how this repository's modules expose them.
* [Dagger 1.0 workspaces (dagger.toml, dagger.lock, dagger-module.toml)](dagger-1-0-workspaces.md) - How Dagger 1.0 splits dagger.json into a workspace config, a lockfile and a module manifest, and how this repository uses them.
* [Publishing on daggerverse.dev](daggerverse-publishing.md) - Rules that decide how a module appears on daggerverse.dev: description source, docstring placement, type-name prefixing, reserved names, tags, and the open 1.0 indexing question.
* [Running Dagger in GitHub Actions](github-actions-integration.md) - How this repo and Daggie-generated workflows call Dagger 1.0 from GitHub Actions: dagger-for-github inputs, version pinning, progress output, LLM access, OIDC env passthrough.
* [Dagger 1.0 beta known issues](known-issues-1-0-beta.md) - Problems hit while moving this repository to Dagger v1.0.0-beta.21, with causes and workarounds.
* [Dagger LLM, workspace agents and MCP](llm-and-mcp.md) - Dagger 1.0's LLM type: a workspace binding, object tools, built-in trace and skill tools, @agent functions, provider configuration, and MCP in both directions.
* [Dagger modules, dependencies and the Daggerverse install path](module-system.md) - How Dagger 1.0 modules declare dependencies (scope clients), are installed and referenced by version, and reach the user's project (Workspace, DefaultPath), as used in this repo.
* [Dagger platform overview](platform.md) - What Dagger is and the building blocks this repo relies on in Dagger 1.0: engine, API, SDKs, workspaces, modules, checks, LLM, Dagger Cloud.
