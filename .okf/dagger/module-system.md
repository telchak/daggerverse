---
type: Reference
title: "Dagger modules, dependencies and the Daggerverse install path"
description: "How dagger.json, dependencies, include, DefaultPath and dagger install/call -m work, as used in this repo."
tags: [dagger, modules]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: deps
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/extending/modules/module-dependencies.mdx
    title: "Dagger docs: module dependencies (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
  - id: remote
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/extending/modules/remote-repositories.mdx
    title: "Dagger docs: remote repositories (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, Core Dagger Knowledge"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
---

# dagger.json

`name`, `engineVersion`, `sdk.source`, `dependencies[]` (`name`, `source`, optional `pin`),
`include[]` (extra paths uploaded with the module, how [agent-base](/agents/agent-base.md) is
shipped), plus `toolchains[]` for toolchain consumers.[^daggie]

# Referencing modules

- Local: `"source": "../gcp-auth"`; remote: `github.com/<owner>/<repo>/<subpath>@<ref>`.[^remote]
- Install into a consumer: `dagger install github.com/telchak/daggerverse/calver@calver/v0.3.2`
  style refs (README shows `@v1.0.0`-like placeholders).
- One-off call: `dagger -m github.com/telchak/daggerverse/goose@<ref> call troubleshoot ...`, or
  locally `dagger -m goose call ...`.
- After editing `dependencies` or the SDK, run `dagger develop` to regenerate `sdk/`.[^deps]

# Host access

Since v0.20, modules cannot read the host (`dag.host()` removed): host files must arrive as
`Directory`/`File` arguments, and `DefaultPath` resolves relative to the module/context
directory, never `~`. See [breaking changes](/dagger/breaking-changes.md).

[^deps]: Dagger docs: module dependencies (v0.21.10)
[^remote]: Dagger docs: remote repositories (v0.21.10)
[^daggie]: Daggie system prompt, Core Dagger Knowledge
