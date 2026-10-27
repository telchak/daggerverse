---
type: Reference
title: "Dagger releases and breaking changes relevant here"
description: "Engine changes from v0.19 to v1.0.0-beta.21 that affected or constrain this repository's modules, including the 0.x to 1.0 migration."
tags: [dagger, versions, gotcha, migration]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-01-24T00:00:00Z
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
    resource: https://github.com/telchak/daggerverse/blob/03534c92052cada32820cc91c9ec48543fabd33a/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt for Dagger 0.x, Breaking Changes (v0.20+)"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
  - id: no-host
    resource: https://github.com/telchak/daggerverse/commit/74849b205d4446822ffb09865915c8495dd8e340
    title: "fix(gcp-auth): replace dag.host() with Directory param"
    author: human:telchak
    last_modified: 2026-03-24T14:57:11+01:00
  - id: migrate
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/config/migrate-dagger-json.mdx
    title: "Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: agents-design
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/hack/designs/workspace-agents.md
    title: "Dagger design: Workspace Agents (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: python
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/reference/sdks/python.mdx
    title: "Dagger docs: Python SDK reference (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
---

| Version | Date | What matters here |
|---------|------|-------------------|
| v0.19.11 | 2026-02 | first Renovate-managed engine |
| v0.20.0 | 2026-02-26 | release notes list GC and log-mode changes;[^v020] in practice modules lost `dag.host()` and `DefaultPath` stopped expanding `~`[^daggie] (gcp-auth fixed 2026-03-24[^no-host]) |
| v0.20.3 / v0.20.5 | 2026-03 / 04 | Speck and runner labels moved here |
| v0.21.0 | 2026-05-22 | caching moved to DagQL (BuildKit solver removed); `generate` functions auto-expose checks; opt-in workspace lockfiles; Python SDK AST analyzer fixes[^v021] |
| v0.21.10 | 2026-10 | last 0.x pin (`main` before the migration) |
| v1.0.0-beta.21 | 2026-10-23 | current pin; see [the migration](/decisions/migrate-to-dagger-1-0.md) |

# 0.x to 1.0: what changed for these modules

- **Configuration:** `dagger.json` split into `dagger.toml`, `dagger.lock` and
  `dagger-module.toml`; generated SDK code is committed and `dagger generate` replaces
  `dagger develop`. See [workspaces](/dagger/dagger-1-0-workspaces.md).[^migrate]
- **Commands:** `dagger init` creates a workspace (`dagger module init` creates a module),
  `dagger install` installs into the workspace (`dagger module client add` adds a dependency),
  `dagger develop` and `dagger toolchain` are removed, `dagger update` fails with a pointer to
  `dagger lock update` / `dagger module update`. Renamed but still accepted: `dagger call` /
  `functions` / `query` → `dagger api call` / `functions` / `query`, `dagger up` → `dagger start`,
  `--mod` → `--load-module`, `--interactive` → `--shell-on-error`, `--cloud` → `--engine=cloud`.[^migrate]
- **API:** `GitRepository.commit` returns a `GitCommit`; output redirected to a file is no longer
  logged; Dagger-in-Dagger is on by default (`experimentalPrivilegedNesting` is ignored,
  `disableDaggerInDagger: true` opts out); `GitRef.commit` → `commitSHA`, `GitRef.ref` → `name`.[^migrate]
- **LLM:** the `Env` type is gone; an LLM binds a `Workspace` and the objects passed to
  `withTools`.[^agents-design] All agents were ported, see [LLM and MCP](/dagger/llm-and-mcp.md).
- **Python SDK:** `@check` functions return `None`; a `dagger.Workspace` argument is injected for
  CLI calls, checks, generators and LLM tools.[^python]
- **Tooling:** `dagger version` and `dagger api functions` reject `--progress`, and non-TTY
  progress defaults to a one-shot report. See [known issues](/dagger/known-issues-1-0-beta.md).

When bumping: read the release notes (`.changes/` in dagger/dagger; the 1.0 betas only have
`.changes/unreleased/`), regenerate with the new CLI, run the whole CI including the agents (LLM
tool schemas come from the engine), and follow
[upgrade the Dagger engine](/playbooks/upgrade-dagger-engine.md).

[^v020]: Dagger v0.20.0 release notes
[^v021]: Dagger v0.21.0 release notes
[^daggie]: Daggie system prompt for Dagger 0.x, Breaking Changes (v0.20+)
[^no-host]: fix(gcp-auth): replace dag.host() with Directory param
[^migrate]: Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)
[^agents-design]: Dagger design: Workspace Agents (v1.0.0-beta.21)
[^python]: Dagger docs: Python SDK reference (v1.0.0-beta.21)
