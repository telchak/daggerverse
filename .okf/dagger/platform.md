---
type: Reference
title: "Dagger platform overview"
description: "What Dagger is and the building blocks this repo relies on: engine, GraphQL API, SDKs, modules, functions, types, caching, Dagger Cloud."
tags: [dagger, platform]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: overview
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/index.mdx
    title: "Dagger docs: Overview (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
  - id: intro
    resource: https://docs.dagger.io/getting-started/introduction/
    title: "Dagger docs: Introduction (docs.dagger.io)"
    author: team:dagger
  - id: intro-main
    resource: https://github.com/dagger/dagger/blob/main/docs/current_docs/getting-started/introduction.mdx
    title: "Dagger docs source: Introduction (main branch)"
    author: team:dagger
    last_modified: 2026-10-10T14:22:01Z
  - id: changelog
    resource: https://github.com/dagger/dagger/blob/main/CHANGELOG.md
    title: "Dagger CHANGELOG"
    author: team:dagger
---

# What it is

Dagger is a platform for automating software delivery: a programmable, local-first, repeatable
and observable alternative to shell scripts and CI YAML. The only host dependency is a container
runtime; the same pipeline runs on a laptop, an AI sandbox, a CI runner or Dagger Cloud.[^overview]
The current docs introduction calls it "the missing software stack for CI": pipeline logic is
decoupled from its environment, run before or after push, cached and traced end to end.[^intro] [^intro-main]

# Building blocks

| Piece | Role here |
|-------|-----------|
| **Engine** | Runs every operation in containers; content-addressed cache (since v0.21.0 implemented in DagQL, BuildKit solver removed[^changelog]) |
| **API** | GraphQL schema, introspectable; [dagger-mcp](/modules/dagger-mcp.md) exposes it to LLMs |
| **SDKs** | Go, Python, TypeScript, PHP, Java, .NET, Elixir, Rust (+ Dang); this repo uses **Python** for modules and ships Go/Python/TypeScript **examples** |
| **Modules** | `dagger.json` + SDK code; loading one extends the API with its functions |
| **Functions** | typed methods, called with `dagger call` or from other modules as `dag.<module>()` |
| **Core types** | `Container`, `Directory`, `File`, `Secret`, `Service`, `CacheVolume`, `GitRepository`, `Env`, `LLM`, `Changeset` |
| **Checks / toolchains** | see [checks and toolchains](/dagger/checks-and-toolchains.md) |
| **LLM** | see [LLM and MCP](/dagger/llm-and-mcp.md) |
| **Dagger Cloud** | traces, module catalog, managed checks; CI passes `DAGGER_CLOUD_TOKEN` |

# Version in use

Every module pins `engineVersion: v0.21.10` and CI uses CLI 0.21.10 (Renovate-managed). Release
history relevant to this repo is in [breaking changes](/dagger/breaking-changes.md); the upcoming
1.0 configuration model is in [Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).

[^overview]: Dagger docs: Overview (v0.21.10)
[^intro]: Dagger docs: Introduction (docs.dagger.io)
[^intro-main]: Dagger docs source: Introduction (main branch)
[^changelog]: Dagger CHANGELOG
