---
type: Reference
title: "Dagger checks and toolchains"
description: "Checks (argument-free validation functions run by dagger check) and toolchains (modules installed for zero-code use), with the customization gotchas."
tags: [dagger, checks, toolchains, platform-engineering]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: checks
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/introduction/core-concepts/checks.mdx
    title: "Dagger docs: Checks (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
  - id: toolchains
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/introduction/core-concepts/toolchains.mdx
    title: "Dagger docs: Toolchains (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, Toolchains and Checks"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
  - id: v021
    resource: https://github.com/dagger/dagger/blob/main/.changes/v0.21.0.md
    title: "Dagger v0.21.0 release notes"
    author: team:dagger
---

# Checks

A check is a function that needs no mandatory arguments, marked `@check` (Python),
`// +check` (Go) or `@check()` (TS). `dagger check` runs all of them concurrently with caching and
exits non-zero on failure; `dagger check -l` lists; glob filters like `dagger check lint-*` or
`pytest:*`.[^checks] Since v0.21.0 every `generate` function also exposes a same-named check
reporting stale generated files (`--no-generate` to skip).[^v021]

# Toolchains

A module installed for direct consumption: `dagger toolchain install github.com/dagger/jest
[--name x]`, then `dagger call <toolchain> <fn>` or `dagger check`. Prefer one toolchain per tool
(black, pytest...) over a monolith.[^toolchains] Platform teams publish org toolchains to
standardize practice.

# Gotchas (from Daggie's knowledge)

- `customizations[]` entries without `"function": ["<fn>"]` target constructor args only; an
  override of a function arg without it is silently ignored.[^daggie]
- In monorepos, every `@check` with a `source` parameter needs a `defaultPath` customization.
- `ignoreChecks` patterns are scoped to the toolchain (no prefix).
- A toolchain-only project's `dagger.json` holds only `name`, `engineVersion`, `toolchains`.

# Relevance here

The build modules ([angular](/modules/angular.md), [python-build](/modules/python-build.md)) do
not mark functions `@check` yet; making them toolchain-ready means adding `@check` and
`DefaultPath(".")` to `lint`/`test`. Daggie generates toolchain configs for users. These are the
"platform engineering" consumption path discussed in the
[article series](/references/dev-to-article-series.md).

[^checks]: Dagger docs: Checks (v0.21.10)
[^toolchains]: Dagger docs: Toolchains (v0.21.10)
[^daggie]: Daggie system prompt, Toolchains and Checks
[^v021]: Dagger v0.21.0 release notes
