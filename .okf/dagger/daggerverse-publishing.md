---
type: Reference
title: "Publishing on daggerverse.dev"
description: "Rules that decide how a module appears on daggerverse.dev: description source, docstring placement, type-name prefixing, reserved names, tags, and the open 1.0 indexing question."
tags: [dagger, publishing, gotcha]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
sources:
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, Module Description and Type Naming"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: docs
    resource: https://github.com/dagger/dagger/blob/v0.21.10/docs/current_docs/extending/modules/daggerverse.mdx
    title: "Dagger docs: Daggerverse (v0.21.10)"
    author: team:dagger
    last_modified: 2026-09-30T13:16:43-03:00
  - id: publishing
    resource: https://github.com/telchak/daggerverse/commit/d44547db1c67ff39bcb75b79a025b688226311ab
    title: "fix: improve daggerverse publishing"
    author: human:telchak
    last_modified: 2026-03-05T14:21:19+01:00
  - id: rename
    resource: https://github.com/telchak/daggerverse/commit/58cb609291099603c16b3154dbbae46f2784f431
    title: "fix(gcp-cloud-run): rename types to avoid redundant daggerverse names"
    author: human:telchak
    last_modified: 2026-03-05T18:54:49+01:00
  - id: speck-init
    resource: https://github.com/telchak/daggerverse/blob/main/speck/src/speck/__init__.py
    title: "speck/src/speck/__init__.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

Learned while publishing this repo in March 2026:[^publishing] [^rename]

1. **The description comes from code**: Python from the `src/<pkg>/__init__.py` docstring, Go from
   the package comment, TypeScript from the main class JSDoc. Template boilerplate ("A generated
   module for...") shows up verbatim if left.[^daggie] In 1.0 `dagger-module.toml` has no
   `description` field at all, so the docstring is the only source.
2. **Python docstring placement:** the description must start on the line after `"""`; text on
   the opening line is skipped. Every module follows this; Speck was fixed during the 1.0
   migration.[^speck-init]
3. **Secondary types get the module name prefixed** (`GcpCloudRun` + `CloudRunService` =
   `GcpCloudRunCloudRunService`). Use short names (`RunService`), but avoid core names
   (`Service`, `Container`, `Directory`, `File`, `Secret`): `type "X" is already defined by module "daggercore"`.
4. Modules are indexed from git refs; this repo publishes `<module>/vX.Y.Z` tags, see
   [release process](/infrastructure/release-process.md).[^docs]

**Open question for 1.0:** 1.0 has no `dagger publish` command, and it was not verified whether
daggerverse.dev indexes modules that have only `dagger-module.toml`. Check the first 1.0 release
on daggerverse.dev; a manual crawl request might be needed. See
[known issues](/dagger/known-issues-1-0-beta.md).

[^daggie]: Daggie system prompt, Module Description and Type Naming
[^docs]: Dagger docs: Daggerverse (v0.21.10)
[^publishing]: fix: improve daggerverse publishing
[^rename]: fix(gcp-cloud-run): rename types to avoid redundant daggerverse names
[^speck-init]: speck/src/speck/__init__.py
