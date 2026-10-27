---
type: Reference
title: "Dagger platform overview"
description: "What Dagger is and the building blocks this repo relies on in Dagger 1.0: engine, API, SDKs, workspaces, modules, checks, LLM, Dagger Cloud."
tags: [dagger, platform]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: intro
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/getting-started/introduction.mdx
    title: "Dagger docs: Introduction (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: glossary
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/glossary.mdx
    title: "Dagger docs: Glossary (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: blog
    resource: https://dagger.io/blog/dagger-10-beta/
    title: "Dagger blog: Dagger 1.0 beta"
    author: team:dagger
  - id: changelog
    resource: https://github.com/dagger/dagger/blob/main/CHANGELOG.md
    title: "Dagger CHANGELOG"
    author: team:dagger
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# What it is

Dagger is a CI orchestration engine: pipelines written once in real code, run identically
before and after push, locally or scaled out on Dagger Cloud, cached automatically and traced end
to end. The only host dependency is a container runtime.[^intro] 1.0 (in beta) organizes a
repository as a **workspace** that installs modules and runs their checks, generators, services
and agents.[^blog] [^glossary]

# Building blocks

| Piece | Role here |
|-------|-----------|
| **Engine** | runs every operation in containers; content-addressed cache in DagQL (BuildKit solver removed in v0.21.0[^changelog]); CLI and engine versions match |
| **API** | GraphQL schema, introspectable; [dagger-mcp](/modules/dagger-mcp.md) exposes it to LLMs |
| **SDKs** | Go, Python, TypeScript, PHP, Java, .NET, Elixir, Rust, Dang; this repo writes modules in **Python** (`github.com/dagger/python-sdk`, itself a module) and ships Go/Python/TypeScript **examples** |
| **Workspace** | `dagger.toml` + `dagger.lock` at the repository root, see [workspaces](/dagger/dagger-1-0-workspaces.md) |
| **Modules** | `dagger-module.toml` + SDK code + committed generated code; loading one extends the API with its functions, see [module system](/dagger/module-system.md) |
| **Functions** | typed methods, called with `dagger api call` or from other modules as `dag.<module>()` |
| **Checks, generators, services** | `dagger check`, `dagger generate`, `dagger start`; installed modules replace 0.x toolchains, see [checks](/dagger/checks-and-toolchains.md) |
| **Core types** | `Container`, `Directory`, `File`, `Secret`, `Service`, `CacheVolume`, `GitRepository`, `Workspace`, `Changeset`, `LLM` (`Env` was removed in 1.0) |
| **LLM** | workspace-bound agents with object tools, `@agent` functions and `dagger agent`, see [LLM and MCP](/dagger/llm-and-mcp.md) |
| **Dagger Cloud** | traces, Cloud Checks (`dagger cloud checks on`), cloud engines; CI passes `DAGGER_CLOUD_TOKEN` |

# Version in use

CLI and engine **1.0.0-beta.21** (`DAGGER_VERSION` in CI, runner label
`dagger-v1.0.0-beta.21`, Renovate-managed).[^ci] History is in
[breaking changes](/dagger/breaking-changes.md); open problems in
[known issues](/dagger/known-issues-1-0-beta.md).

[^intro]: Dagger docs: Introduction (v1.0.0-beta.21)
[^glossary]: Dagger docs: Glossary (v1.0.0-beta.21)
[^blog]: Dagger blog: Dagger 1.0 beta
[^changelog]: Dagger CHANGELOG
[^ci]: CI workflow
