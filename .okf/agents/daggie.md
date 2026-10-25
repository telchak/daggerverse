---
type: AI Agent
title: "Daggie (Dagger CI specialist agent)"
description: "AI agent that creates, explains, debugs and reviews Dagger 1.0 (and 0.x) modules and pipelines across SDKs, backed by dagger-mcp and runtime-cloned reference modules."
resource: https://github.com/telchak/daggerverse/tree/main/daggie
tags: [agent, llm, dagger]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/main.py
    title: "daggie/src/daggie/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/README.md
    title: "daggie/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/daggie/src/daggie/prompts
    title: "daggie prompt files"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/dagger-module.toml
    title: "daggie/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/911b51e41b374414e06694d2515849504f3ec03a
    title: "feat(daggie): add Daggie agent"
    author: human:telchak
    last_modified: 2026-02-24T11:01:00+01:00
  - id: block
    resource: https://github.com/telchak/daggerverse/commit/6c940b919615dc3e0efbe4211c3adccb8372dce6
    title: "fix(daggie): block only existing entrypoints to prevent LLM hallucination"
    author: human:telchak
    last_modified: 2026-02-24T12:21:56+01:00
  - id: enhance
    resource: https://github.com/telchak/daggerverse/commit/40677a3b86621afc3c7622a710b77d6e83463331
    title: "feat(daggie): Enhance Daggie agent with more accurate instructions and new arguments"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
  - id: system
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Entrypoints

`assist(assignment, assignment_file?)`, `explain(question)`, `debug(error_output)`, `review`,
`read_module(url)`, `suggest_github_fix`, `develop_github_issue`, and `agent` (`@agent`).[^main]
`explain` and `review` block the destructive tools; `debug` keeps the last 8000 characters of the
error output. `.agent-tests` lists `assist explain debug`.

Constructor: `source` (`DefaultPath("/")`), `module_urls: list[str]`, `self_improve` (in
`_FIELDS`). Runs on the Python SDK runtime with `_agent_base` included.[^manifest]

# Reference modules at runtime

`--module-urls` accepts `url`, `url#branch` or `url#branch:path`. Daggie clones each with
`dag.git(url).branch(branch, no_lock=True)` (`no_lock` keeps them out of the caller's
`dagger.lock`), finds modules by their manifest (`dagger-module.toml`, or `dagger.json` for 0.x),
skipping generated `sdk/` and `clients/` directories, and reads the manifests, `*.dang`,
`src/*/__init__.py`, `src/**/main.py`, `src/**/main.ts` and `main.go` (each truncated at 6000
characters) into the prompt. It also lists the remote tags of `dagger/dagger-for-github` with
`git ls-remote` so the workflows it writes use the latest action version, falling back to
`v8.4.1`.[^main]

# Configuration specifics

- Context files: `("DAGGIE.md", "DAGGER.md", "AGENT.md", "CLAUDE.md")`.
- MCP: [dagger-mcp](/modules/dagger-mcp.md) for assist, explain and debug, run from
  `dag.dagger_mcp().container()` with Dagger-in-Dagger access and `live=True`, and called through
  `mcp(server="dagger", ...)`. See [task-scoped MCP](/patterns/task-scoped-mcp.md).
- Daggie overrides the shared `BLOCKED_ENTRYPOINTS` with its own list
  (`assist, review, develop_github_issue, suggest_github_fix` plus `explain, debug, read_module`)
  because blocking functions that do not exist on the class makes the LLM aware of them and
  causes hallucinated calls.[^block] See [blocked functions](/patterns/blocked-functions.md).

# The system prompt is a Dagger knowledge base

`prompts/system_prompt.md` was rewritten for Dagger 1.0: workspaces and modules
(`dagger.toml`, `dagger-module.toml`, committed generated code), the 1.0 Python SDK (Workspace
arguments, `@check` returning None), checks, generators, services and collections, installed
modules replacing toolchains, the 1.0 breaking changes and CLI, daggerverse descriptions from
`__init__.py` docstrings, secondary type naming, and GitHub Actions without `verb: version` and
with `--allow-llm`.[^system] Those facts are mirrored in this bundle under
[dagger/](/dagger/index.md); when one changes, update both.

Added 2026-02-24;[^added] toolchain/check knowledge added with Speck on 2026-03-21; enhanced
2026-03-26;[^enhance] ported to 1.0 on 2026-10-24.

[^main]: daggie/src/daggie/main.py
[^manifest]: daggie/dagger-module.toml
[^added]: feat(daggie): add Daggie agent
[^block]: fix(daggie): block only existing entrypoints to prevent LLM hallucination
[^enhance]: feat(daggie): Enhance Daggie agent with more accurate instructions and new arguments
[^system]: Daggie system prompt
