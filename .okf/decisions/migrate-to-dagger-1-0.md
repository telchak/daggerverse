---
type: Decision
title: "Migrate every module to Dagger 1.0 (beta)"
description: "On 2026-10-24 all modules moved from Dagger v0.21.10 to v1.0.0-beta.21: one root workspace with a Python SDK scope per module, committed generated code, agents on the SDK runtime, 1.0 features adopted, and a major release of every module."
tags: [decision, dagger, migration, workspace]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: blog
    resource: https://dagger.io/blog/dagger-10-beta/
    title: "Dagger blog: Dagger 1.0 beta"
    author: team:dagger
  - id: migrate
    resource: https://github.com/dagger/dagger/blob/v1.0.0-beta.21/docs/current_docs/config/migrate-dagger-json.mdx
    title: "Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)"
    author: team:dagger
    last_modified: 2026-10-23T09:33:31+02:00
  - id: python-sdk
    resource: https://github.com/dagger/python-sdk/blob/v1.2.0/README.md
    title: "dagger/python-sdk README (v1.2.0)"
    author: team:dagger
  - id: workspace-toml
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (this repository)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: semver
    resource: https://github.com/telchak/daggerverse/blob/main/semver/src/semver/main.py
    title: "semver/src/semver/main.py (bump rules)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Context

Dagger 1.0 (beta) reorganizes a repository as a workspace that installs modules and runs their
checks, generators and agents.[^blog] 1.0 still runs 0.x projects, but the module surface
changed: `Env` is gone (every agent here built on it), `@check` returns None, and migrated
modules commit their generated code.[^migrate] The maintainer asked to move every module to 1.0
and use the new features.

# Decision

1. **One workspace at the repository root.** `dagger.toml` installs the Python SDK and declares
   one scope per module; a module's dependencies are its scope's `clients`. There is no workspace
   main module: modules stay independent and are released separately.[^workspace-toml]
   `dagger workspace migrate` did not apply (no root `dagger.json`), so each module was migrated
   with `dagger module migrate`, dependencies first.[^python-sdk]
2. **Static entrypoints for the plain modules and `tests`**, with `sdk/`, `clients/` and
   `uv.lock` committed. CI's new `check` job runs `dagger check`, whose staleness check fails when
   committed code differs from `dagger generate`.[^ci]
3. **Agents stay on the Python SDK runtime** (`legacyRuntime = true`): they bind themselves with
   `dag.current_node()` and ship `_agent_base` through `include`, neither of which works behind a
   static entrypoint.
4. **Agents ported to the 1.0 LLM API**: workspace binding, object tools, results from the final
   reply or the edited workspace, JSON replies for routers and suggest-fix, and MCP through a
   [stdio driver](/decisions/mcp-exec-driver.md). Goose moved onto
   [agent-base](/agents/agent-base.md) in the same change.
5. **1.0 features adopted:** workspace checks in [angular](/modules/angular.md) and
   [python-build](/modules/python-build.md) (install the module, run `dagger check`, no code);
   `check_*` wrappers in the [tests module](/infrastructure/tests-module.md); `@agent` functions
   in Angie, Monty and Daggie for `dagger agent`; Daggie's knowledge and dagger-mcp's guides
   rewritten for 1.0.
6. **`examples/` stay on `dagger.json`:** 1.0 loads them against the migrated modules, which
   avoids committing generated code for 48 example modules.
7. **Release:** one `feat!:` commit, so the semver module bumps every module's major version
   (0.x to `v1.0.0`).[^semver] The 0.x tags stay for Dagger 0.x users.
8. **Tooling:** runners labelled `dagger-v1.0.0-beta.21`, `DAGGER_PROGRESS=plain`,
   dagger-for-github without `verb: version`, and Renovate on `github-tags` with semver
   versioning so it sees the beta tags.[^ci]

# Alternatives considered

- **Keep `dagger.json` everywhere:** 1.0 loads it, but without workspace features, and the agents
  had to be rewritten anyway because `Env` was removed.
- **Static entrypoints for agents:** blocked by `dag.current_node()` and `include` (point 3).

# Consequences

- Beta engine with open problems: see [known issues](/dagger/known-issues-1-0-beta.md).
- Every engine bump also needs a regeneration commit, see
  [upgrade the Dagger engine](/playbooks/upgrade-dagger-engine.md).
- The ARC runner scale set labelled `dagger-v1.0.0-beta.21` must exist before merging, see
  [self-hosted runners](/decisions/self-hosted-dagger-runners.md).
- Whether daggerverse.dev indexes `dagger-module.toml` modules is unverified, see
  [publishing](/dagger/daggerverse-publishing.md).
- Contributors on Windows cannot get a green local `dagger check`.

[^blog]: Dagger blog: Dagger 1.0 beta
[^migrate]: Dagger docs: Migrate to Dagger 1.0 (v1.0.0-beta.21)
[^python-sdk]: dagger/python-sdk README (v1.2.0)
[^workspace-toml]: dagger.toml (this repository)
[^ci]: CI workflow
[^semver]: semver/src/semver/main.py (bump rules)
