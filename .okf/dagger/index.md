# Dagger platform

Upstream Dagger knowledge this repo depends on, pinned to v0.21.10.

* [Dagger releases and breaking changes relevant here](breaking-changes.md) - Engine changes between v0.19 and v0.21.10 that affected or constrain this repository's modules.
* [Dagger checks and toolchains](checks-and-toolchains.md) - Checks (argument-free validation functions run by dagger check) and toolchains (modules installed for zero-code use), with the customization gotchas.
* [Upcoming: Dagger 1.0 workspaces (dagger.toml)](dagger-1-0-workspaces.md) - Dagger's main branch splits dagger.json into dagger-module.toml (module manifest) and dagger.toml (workspace config), with migrate commands; not released as of v0.21.10. *(draft)*
* [Publishing on daggerverse.dev](daggerverse-publishing.md) - Rules that decide how a module appears on daggerverse.dev: description source, docstring placement, type-name prefixing, reserved names, tags.
* [Running Dagger in GitHub Actions](github-actions-integration.md) - How this repo and Daggie-generated workflows call Dagger from GitHub Actions: dagger-for-github inputs, version pinning, OIDC env passthrough.
* [Dagger LLM, Env and MCP](llm-and-mcp.md) - Dagger's native LLM type: environments with typed inputs/outputs, tool use over Dagger functions, blocked functions, and MCP in both directions.
* [Dagger modules, dependencies and the Daggerverse install path](module-system.md) - How dagger.json, dependencies, include, DefaultPath and dagger install/call -m work, as used in this repo.
* [Dagger platform overview](platform.md) - What Dagger is and the building blocks this repo relies on: engine, GraphQL API, SDKs, modules, functions, types, caching, Dagger Cloud.
