# CLAUDE.md

Monorepo of reusable Dagger modules and AI agents (Python SDK), published on daggerverse.dev,
on Dagger 1.0. The repository root is a Dagger workspace (`dagger.toml`, `dagger.lock`): every
top-level directory with a `dagger-module.toml` is a module and a Python SDK scope there,
released independently as `<module>/vX.Y.Z` from Conventional Commits. Tests live in `tests/`
and run through the single workflow `.github/workflows/ci.yml`.

## Knowledge base: read `.okf/` first

This project keeps its shared knowledge as an [OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format)
bundle in `.okf/`: architecture, every module and agent, CI and release mechanics, decisions
reconstructed from git history, Dagger platform knowledge pinned to the engine version in use,
playbooks, and known gotchas.

**Before a task:** read `.okf/index.md`, then follow links only into the concepts the task
touches (e.g. `.okf/modules/gcp-auth.md`, `.okf/agents/agent-base.md`,
`.okf/infrastructure/ci-pipeline.md`, `.okf/playbooks/add-a-new-module.md`). Weigh what you read:
`status: draft` or `deprecated`, a `stale_after` in the past, or no `verified` entry all mean
"check against the code before relying on this". A broken link is knowledge not written yet, not
an error. When the bundle and the code disagree, the code wins: fix the bundle.

**After a change:** if it affects anything documented (a module's functions or defaults, an
agent's behaviour or prompts, CI, release, Renovate, conventions, the Dagger version) or you
learned something durable (a gotcha, the reason behind a choice, a debugging recipe), update the
bundle in the same change:

- Edit the matching concept: refresh its body, set `generated: { by: claude-code/<version>, at: <now, ISO 8601> }`,
  update `sources` (repo files as `https://github.com/telchak/daggerverse/blob/main/<path>`,
  commits as `.../commit/<sha>`, with `last_modified`), fix cross-links.
- New module, agent, decision or playbook: new concept file (one concept per file, required
  `type`, plus `title`, `description`, `tags`), and add it to its directory `index.md` and to
  the root `.okf/index.md`.
- Removed or replaced things: set `status: deprecated` and link the replacement; never delete
  silently.
- Append a dated entry to `.okf/log.md` only for lifecycle events (concept created, deprecated,
  superseded, regenerated after its source changed, verified). Routine edits get no log entry.
- Never add a `verified` entry yourself; that is for a human (`human:<id>`) or a process that
  actually checked the content.
- Keep `.okf/conventions/documentation-drift.md` current when README/CONTRIBUTING disagree with code.

**Before committing** bundle changes, validate (must pass with no warnings):

```bash
uv run .claude/skills/validate/scripts/okf_validate.py .okf --strict
```

Vendored skills (`.claude/skills/`, from okf-skills): `/okf` (produce, maintain, consume),
`/validate`, `/visualize`, `/backfill`. Spec: `.claude/skills/okf/reference/SPEC.md`.

## Working rules for this repo

- Commits: `<type>(<module>): <description>`. `feat` = minor, `fix|perf|refactor` = patch,
  `!`/`BREAKING CHANGE` = major. Bump detection reads all commits since a module's last tag
  (see `.okf/modules/semver.md`).
- A new module (`dagger module init python --name <m> --path <m>`) needs its scope in
  `dagger.toml`, `README.md`, `examples/`, a `Tests.<module>` function in
  `tests/src/tests/main.py`, and its module added to the tests scope's `clients`. Keep source
  files under 600 lines.
- A module's dependencies are its scope's `clients` in `dagger.toml`, not the manifest.
- After changing a function signature, a scope's clients or the Dagger version, run
  `dagger generate -y` and commit `sdk/`, `clients/` and `uv.lock`: the generated entrypoint
  bakes in the module's types, and `dagger check` (CI) fails when they are stale. Never edit
  `sdk/` or `clients/` by hand.
- The daggerverse description comes from `src/<pkg>/__init__.py`'s docstring, starting on the
  line after the opening quotes (`dagger-module.toml` has no description).
- Agents run on the Python SDK runtime (`legacyRuntime = true` in their scope settings),
  because they bind themselves to their LLM with `dag.current_node()`. Block tools by their
  Python names through `llm_helpers.tool_exclusions` (the engine wants camelCase and ignores
  unknown names); read results with `llm_helpers.reply` / `edited_directory`, which run the
  loop; keep the efficiency budget in system prompts.
- MCP servers go through `agent_base.mcp_stdio` (a catalog in the system prompt plus the
  agent's `mcp` tool), not `LLM.with_mcp_server`, which hangs on the second step in
  v1.0.0-beta.21.
- The Dagger version (`DAGGER_VERSION`, `runs-on: dagger-v*`, the README badge and the
  dagger-for-github snippets in READMEs and Daggie's system prompt) is bumped together by
  Renovate; do not change one alone, and update CONTRIBUTING's version by hand. A bump also needs
  `dagger generate -y` with the new CLI, pushed onto the Renovate PR.

Tests: `dagger api call -m ./tests <module>`, `dagger check` (generated code is current) and
`dagger check -m ./tests --generated=false` (credential-free module tests only); see `.okf/playbooks/run-tests-locally.md`.
