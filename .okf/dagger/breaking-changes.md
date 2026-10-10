---
type: Reference
title: "Dagger releases and breaking changes relevant here"
description: "Engine changes between v0.19 and v0.21.10 that affected or constrain this repository's modules."
tags: [dagger, versions, gotcha]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: v020
    resource: https://github.com/dagger/dagger/blob/main/.changes/v0.20.0.md
    title: "Dagger v0.20.0 release notes"
    author: team:dagger
  - id: v021
    resource: https://github.com/dagger/dagger/blob/main/.changes/v0.21.0.md
    title: "Dagger v0.21.0 release notes"
    author: team:dagger
  - id: daggie
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, Breaking Changes (v0.20+)"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
  - id: no-host
    resource: https://github.com/telchak/daggerverse/commit/74849b205d4446822ffb09865915c8495dd8e340
    title: "fix(gcp-auth): replace dag.host() with Directory param"
    author: human:telchak
    last_modified: 2026-03-24T14:57:11+01:00
---

| Version | Date | What matters here |
|---------|------|-------------------|
| v0.19.11 | 2026-02 | first Renovate-managed engine; CONTRIBUTING still quotes it |
| v0.20.0 | 2026-02-26 | release notes list GC and log-mode changes;[^v020] in practice modules lost `dag.host()` and `DefaultPath` stopped expanding `~`[^daggie] (gcp-auth fixed 2026-03-24[^no-host]) |
| v0.20.3 / v0.20.5 | 2026-03 / 04 | Speck and runner labels moved here |
| v0.21.0 | 2026-05-22 | caching moved to DagQL (BuildKit solver removed); `generate` functions auto-expose checks; opt-in workspace lockfiles (`--lock live|pinned|frozen`, `.dagger/lock`); Python SDK AST analyzer fixes[^v021] |
| v0.21.10 | 2026-10 | current pin |

When bumping: read `.changes/<version>.md` in dagger/dagger, run the whole CI (all agents) since
LLM tool schemas come from the engine, and follow [upgrade the Dagger engine](/playbooks/upgrade-dagger-engine.md).

[^v020]: Dagger v0.20.0 release notes
[^v021]: Dagger v0.21.0 release notes
[^daggie]: Daggie system prompt, Breaking Changes (v0.20+)
[^no-host]: fix(gcp-auth): replace dag.host() with Directory param
