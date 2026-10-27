# Daggerverse - Reusable Dagger Modules

[![CI](https://github.com/telchak/daggerverse/actions/workflows/ci.yml/badge.svg)](https://github.com/telchak/daggerverse/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Dagger](https://img.shields.io/static/v1?label=Dagger&message=v1.0.0-beta.21&color=1a1a2e)](https://dagger.io)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=telchak_daggerverse&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=telchak_daggerverse)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=telchak_daggerverse&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=telchak_daggerverse)

A collection of small, independent, reusable [Dagger](https://github.com/dagger/dagger) modules and AI agents for CI/CD pipelines. Built with the [Dagger SDK](https://docs.dagger.io) and published on the [Daggerverse](https://daggerverse.dev).

## Modules

Reusable building blocks for CI/CD pipelines. Each module is independent and focused on a single concern.

| Module | Description |
|--------|-------------|
| [**calver**](calver/) | Calendar Versioning utilities |
| [**gcp-auth**](gcp-auth/) | GCP authentication (OIDC, Workload Identity Federation, Service Account) |
| [**gcp-artifact-registry**](gcp-artifact-registry/) | Artifact Registry container image operations |
| [**gcp-cloud-run**](gcp-cloud-run/) | Cloud Run service and job deployment |
| [**gcp-vertex-ai**](gcp-vertex-ai/) | Vertex AI model deployment |
| [**gcp-firebase**](gcp-firebase/) | Firebase Hosting deployment and preview channels |
| [**angular**](angular/) | Angular build, lint, test, and serve utilities |
| [**health-check**](health-check/) | HTTP and TCP container health checking |
| [**oidc-token**](oidc-token/) | OIDC token exchange utilities |
| [**python-build**](python-build/) | Python build, lint, test, and typecheck utilities |
| [**semver**](semver/) | Semantic Versioning with Conventional Commits |
| [**dagger-mcp**](dagger-mcp/) | MCP server for Dagger engine introspection — schema, GraphQL queries, SDK guidance |

## AI Agents

AI-powered development and operations agents built with Dagger's LLM support. Each agent provides specialized entrypoints (`assist`, `review`, `build`, `write-tests`, `upgrade`, `develop-github-issue`, `task`) and uses MCP servers for extended capabilities.

### [Angie](angie/) — Angular Development Agent

Code analysis, reviews, test writing, building, and upgrades for Angular projects.

| MCP Server | Package | Description |
|------------|---------|-------------|
| `angular` | [`@angular/cli mcp`](https://angular.dev/ai/mcp) | Built-in Angular CLI MCP — code generation, modernization, best practices, documentation search |

### [Monty](monty/) — Python Development Agent

Linting, formatting, testing, package auditing, and code reviews for Python projects.

| MCP Server | Package | Description |
|------------|---------|-------------|
| `python-lft` | [`python-lft-mcp[tools]`](https://github.com/Agent-Hellboy/python-lft-mcp) | Lint (ruff), format (black/ruff), test (pytest), and type-check (mypy). Installed from GitHub (not yet published to PyPI). |
| `pypi` | [`pypi-query-mcp-server`](https://github.com/loonghao/pypi-query-mcp-server) | Package intelligence — version tracking, dependency analysis, download stats |

### [Goose](goose/) — GCP Operations Agent

Deployment, troubleshooting, and observability across Cloud Run, Firebase Hosting, Vertex AI, and Artifact Registry.

| MCP Server | Package | Description |
|------------|---------|-------------|
| `gcloud` | [`@google-cloud/gcloud-mcp`](https://github.com/googleapis/gcloud-mcp) | Cloud Logging, Cloud Monitoring, Cloud Trace, Cloud Storage, and full gcloud CLI access |

Goose also integrates the [Google Developer Knowledge API](https://developers.googleblog.com/introducing-the-developer-knowledge-api-and-mcp-server/) as native Dagger functions (`search_gcp_docs`, `get_gcp_doc`, `batch_get_gcp_docs`) for real-time GCP documentation search. These are exposed as regular functions rather than an MCP server because Dagger currently only supports stdio-based MCP servers, and the Developer Knowledge API is HTTP-based.

### [Daggie](daggie/) — Dagger CI Specialist Agent

Creating, explaining, and debugging Dagger modules and pipelines across all SDKs (Python, TypeScript, Go).

| MCP Server | Module | Description |
|------------|--------|-------------|
| `dagger` | [`dagger-mcp`](dagger-mcp/) | Live Dagger engine introspection — schema, GraphQL queries, SDK translation guidance |

Daggie can also clone and read reference Dagger modules at runtime via `--module-urls` to learn patterns from existing implementations.

### [Speck](speck/) — Spec-Driven Development Agent

Turns a prompt or GitHub issue into a specification, a technical plan, and a JSON task decomposition that assigns each task to an agent and a model, ready for a GitHub Actions matrix. Inspired by [spec-kit](https://github.com/github/spec-kit). No MCP servers.

### Shared Agent Base (`_agent_base/`)

All five agents share a common Python package ([`_agent_base/`](_agent_base/)) that provides the duplicated logic:

| Module | Purpose |
|--------|---------|
| `constants` | Blocked entrypoints and destructive tool lists |
| `workspace` | `read_file`, `edit_file`, `write_file`, `glob`, `grep` implementations on the LLM's workspace |
| `llm_helpers` | LLM builders (entrypoints, task sub-agent, `@agent`), tool exclusions, context file reader |
| `mcp_stdio` | MCP servers: tool catalog in the system prompt and the `mcp` tool (a one-shot stdio call per request) |
| `github_tools` | `suggest-github-fix` (posts PR code suggestions), `develop-github-issue` |
| `routing` | Router reply parsing and function dispatch |

Each agent's `main.py` is a thin wrapper that defines only what's unique: class name, constructor fields, MCP servers, prompt path, context file priority, and entrypoint signatures (Goose adds its GCP tools). The shared package is included via the `include` field of the agent's `dagger-module.toml` and installed as a local Python dependency.

### Shared patterns

All agents follow the same design:
- **Workspace tools** (`read_file`, `edit_file`, `write_file`, `glob`, `grep`) for interacting with source code
- **Context files** for per-repo configuration (e.g. `ANGIE.md`, `MONTY.md`, `GOOSE.md`)
- **GitHub integration** via `develop-github-issue` to read an issue, route it to the right entrypoint, and open a PR
- **Blocked tools** — each agent binds itself to its LLM (`with_tools(dag.current_node(), except_=[...])`) and hides its own entrypoints to prevent recursion
- **`dagger agent` ready** — Angie, Monty and Daggie expose an `@agent` function: install one with `dagger module install` and work with it interactively in `dagger agent`, on your workspace

### Self-Improvement

All agents support a `--self-improve` constructor flag that creates a learning loop: the agent updates context files with discoveries made during the session, so it gets smarter across iterations.

| Mode | Behavior |
|------|----------|
| `off` (default) | No change — current behavior |
| `write` | Agent updates context files in the returned workspace directory |
| `commit` | Agent updates context files and creates a git commit in the returned workspace directory |

```bash
# Monty learns about your project as it works
dagger api call monty --self-improve=write assist \
  --source . \
  --assignment "Add a FastAPI health endpoint"
```

The agent writes to **two** context files:
- **Agent-specific file** (e.g. `MONTY.md`) — language/framework patterns, stack-specific conventions, tool gotchas
- **Shared file** (`AGENTS.md`) — project architecture, cross-cutting conventions, CI/CD patterns, team preferences

This separation prevents agent-specific knowledge from polluting shared context. When Monty discovers a Python async pattern, it goes in `MONTY.md`. When it discovers the project's folder structure, it goes in `AGENTS.md`.

**Reading** merges both files: the agent reads its own file (e.g. `MONTY.md`) plus the shared file (`AGENTS.md`, with `AGENT.md` and `CLAUDE.md` as legacy fallbacks). This applies to all directory-returning entrypoints (`assist`, `build`, `write-tests`, `upgrade`, `debug`).

## Installation

The modules target **Dagger 1.0** (`dagger-module.toml`). Install one into your workspace (`dagger.toml`), with a version:

```bash
dagger module install github.com/telchak/daggerverse/calver@v1.0.0
dagger module install github.com/telchak/daggerverse/gcp-auth@v1.0.0
```

Each module is released with its own tags (`calver/v1.0.0`): `@v1.0.0` selects that module's tag. Dagger 1.0 also accepts `@v1.0` (latest patch) and `@v1` (latest minor); the resolved tag is recorded in `dagger.lock` and refreshed with `dagger lock update`. Without a version you get the module's latest release; `@main` tracks the main branch (not recommended for production).

To call a module from your own module's code, add it as a client (dependency), from your module's directory:

```bash
dagger module client add github.com/telchak/daggerverse/calver@v1.0.0 --sdk=python
```

Releases tagged before the Dagger 1.0 migration (`<module>/v0.x`) still use `dagger.json` and work with Dagger 0.x.

## Quick Start

### CalVer - Generate versions

```bash
# Generate date-based version
dagger api call calver generate --format="YYYY.0M.0D"
# Output: 2026.02.11

# Auto-increment from git tags
dagger api call calver generate --source=. --format="v.YYYY.MM.MICRO"
# Output: v.2026.2.3
```

### GCP Auth - Authenticate

```bash
# Verify credentials
dagger api call gcp-auth verify-credentials \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS
```

### Health Check - Verify containers

```bash
# HTTP health check
dagger api call health-check http \
  --container=FROM_BUILD \
  --port=8080 \
  --path=/health
```

### Goose - GCP operations

```bash
# Troubleshoot a Cloud Run service
dagger api call goose troubleshoot \
  --google-cloud-dir ~/.config/gcloud \
  --issue "Service returning 503 errors"

# Deploy with an AI agent
dagger api call goose deploy \
  --google-cloud-dir ~/.config/gcloud \
  --assignment "Deploy image us-docker.pkg.dev/my-project/repo/app:latest as my-service" \
  --source .
```

### Monty - Python development

```bash
# Review Python code
dagger api call monty review --source .

# General assistance
dagger api call monty assist \
  --source . \
  --assignment "Add a FastAPI endpoint with Pydantic validation"
```

### Daggie - Dagger CI development

```bash
# Create a Dagger module for your project
dagger api call daggie assist \
  --source . \
  --assignment "Create a Dagger module for building and testing this project"

# Explain a Dagger concept
dagger api call daggie explain \
  --question "How does caching work in Dagger?"

# Debug a pipeline error
dagger api call daggie debug \
  --source . \
  --error-output "$(dagger api call build 2>&1)"
```

### Angie - Angular development

```bash
# Review Angular code
dagger api call angie review --source .

# Build an Angular project
dagger api call angie build --source .
```

## Architecture

```
daggerverse/
├── dagger.toml             # Dagger 1.0 workspace: every module's Python SDK scope
├── dagger.lock             # pinned images, Git refs and SDK versions
├── _agent_base/            # Shared Python package for coding agents
├── angular/                # Angular build, lint, test, serve
├── calver/                 # Calendar versioning
├── dagger-mcp/             # MCP server for Dagger engine introspection
├── gcp-auth/               # GCP authentication (base)
├── gcp-artifact-registry/  # Artifact Registry operations
├── gcp-cloud-run/          # Cloud Run deployment
├── gcp-vertex-ai/          # Vertex AI deployment
├── gcp-firebase/           # Firebase Hosting deployment
├── health-check/           # HTTP and TCP health checks
├── oidc-token/             # OIDC token utilities
├── python-build/           # Python build, lint, test, typecheck
├── semver/                 # Semantic versioning
├── angie/                  # Angular development agent
├── daggie/                 # Dagger CI specialist agent
├── monty/                  # Python development agent
├── goose/                  # GCP operations agent
├── speck/                  # Spec-driven development agent
└── tests/                  # Centralized test suite
```

Modules are designed to be independent, with one exception: `gcp-auth` depends on `oidc-token` for GitHub Actions OIDC token exchange. GCP modules accept pre-authenticated containers from `gcp-auth`:

```
oidc-token ──> gcp-auth
                 │ provides authenticated gcloud containers
                 ├──> gcp-artifact-registry
                 ├──> gcp-cloud-run
                 ├──> gcp-vertex-ai
                 └──> gcp-firebase (OIDC, service account, or access token)

goose ──> GCP operations agent that orchestrates:
  ├──> gcp-cloud-run
  ├──> gcp-artifact-registry
  ├──> gcp-firebase
  ├──> gcp-vertex-ai
  ├──> health-check
  └──> gcloud MCP (Cloud Logging, Monitoring, Trace, GCS)

_agent_base ──> Shared agent logic (workspace, MCP, GitHub, LLM, routing), used by goose and:
  ├──> angie (Angular development agent)
  │      ├──> angular (deterministic build, lint, test, serve)
  │      └──> Angular CLI MCP
  ├──> daggie (Dagger CI specialist agent)
  │      └──> dagger-mcp (Dagger engine introspection MCP)
  ├──> monty (Python development agent)
  │      ├──> python-build (deterministic build, lint, test, typecheck)
  │      ├──> python-lft MCP (linting, formatting, testing)
  │      └──> pypi-query MCP (package intelligence)
  └──> speck (spec-driven development agent)

angular, calver, dagger-mcp, health-check, oidc-token, python-build, semver (standalone)
```

## Testing

Tests are centralized in the `tests/` module. This keeps the main modules clean and tests the public API exactly as users would.

### Run Tests Locally

```bash
# Workspace check: the committed generated code matches `dagger generate`
dagger check

# Module tests that need no credentials, as checks (calver, health-check,
# oidc-token, angular, python-build, dagger-mcp)
dagger check -m ./tests --generated=false

# Tests without credentials (calver, health-check, oidc-token)
dagger api call -m ./tests all-no-credentials

# All GCP tests (require OIDC credentials)
dagger api call -m ./tests all-gcp \
  --workload-identity-provider="..." \
  --service-account="..." \
  --project-id="..." \
  --repository="..." \
  --oidc-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
  --oidc-url=env:ACTIONS_ID_TOKEN_REQUEST_URL
```

### CI

Tests run automatically on push to `main`, pull requests, and manual dispatch via GitHub Actions. The pipeline has 7 stages:

| Job | Description |
|-----|-------------|
| `discover` | Auto-detects all modules and agents (classifies by `src/*/prompts/`), reads `.agent-tests` for per-agent test lists |
| `validate` | Checks every module for required files (`dagger-module.toml`, a package docstring description, `README.md`, `examples/`), loads functions, warns on source files exceeding 600 lines |
| `check` | Runs `dagger check`: the committed generated code (`sdk/`, `clients/`, entrypoint types) of every module must match `dagger generate` |
| `test-modules` | Matrix job — tests each non-agent module in parallel. GCP modules (`gcp-*`) receive OIDC credentials automatically |
| `test-agents` | Matrix job — tests each agent entrypoint in parallel (e.g. `angie-assist`, `goose-deploy`). Agents with `.agent-gcp` marker receive OIDC credentials |
| `test-angie-github-issue` | Dedicated job for `develop-github-issue` end-to-end test (creates a PR, then cleans it up) |
| `release` | Runs on `main` only — tags changed modules with semver (via Conventional Commits) |

### Validation Pipeline

| Check | Type | Description |
|-------|------|-------------|
| dagger-module.toml exists | Error | Required for all modules |
| Package docstring | Error | `src/<package>/__init__.py` docstring: the description shown on the Daggerverse |
| README.md exists | Error | Required documentation |
| examples/ directory exists | Error | Required for usage examples |
| Line count < 600 | Warning | Keep source files concise |
| Function docstrings | Warning | All public functions documented |
| Emojis in code | Warning | Avoid emojis for clean output |
| Module loads | Error | Validates module syntax |
| Example modules load | Error | Validates examples work |

## Publishing

### Module Versioning

Each module is versioned independently using semantic versioning (`vMAJOR.MINOR.PATCH`), with tags prefixed by the module name:

```
calver/v1.0.0
gcp-auth/v1.2.3
health-check/v0.5.0
```

### Automatic Releases

The **Release Modules** workflow runs on every push to main and:
- Detects which modules have changes since their last tag
- Analyzes commit messages using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)
- Automatically determines version bump (major/minor/patch)
- Creates per-module semver tags

Commit message format:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` | Minor | `feat(auth): add OIDC support` |
| `fix:`, `perf:`, `refactor:` | Patch | `fix(cloud-run): handle timeout` |
| `chore:`, `docs:`, `ci:`, `test:`, `build:`, `style:` | Patch (default) | `chore: update dependencies` |
| `feat!:` or `BREAKING CHANGE:` | Major | `feat!: remove deprecated API` |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including:

- Development setup and prerequisites
- How to add a new module (required files, tests, CI integration)
- Commit message conventions (Conventional Commits)
- Pull request process and review guidelines
- Module design principles and naming conventions

## Creating a New Agent

To create a new coding agent (e.g., "Rusty" for Rust) based on the shared `_agent_base` package:

1. **Initialize the module** from the repository root. This registers its Python SDK scope in `dagger.toml`:
   ```bash
   dagger module init python --name rusty --path rusty
   ```

2. **Put the agent on the Python SDK's runtime.** Agents bind themselves to their LLM with `dag.current_node()`, which a generated entrypoint cannot answer. In `dagger.toml`:
   ```toml
   [sdks.python.scopes.rusty.settings]
   legacyRuntime = true
   ```

3. **Add the GitHub client**, from the module directory:
   ```bash
   cd rusty
   dagger module client add github.com/kpenfound/dag/github-issue@b316e472d3de5bb0e54fe3991be68dc85e33ef38 --sdk=python
   ```

4. **Add the shared base**: `include = ["../_agent_base"]` in `rusty/dagger-module.toml`, and the editable dependency in `rusty/pyproject.toml`:
   ```toml
   dependencies = ["dagger-io", "agent-base"]

   [tool.uv.sources]
   agent-base = { path = "../_agent_base", editable = true }
   ```

5. **Write `rusty/src/rusty/main.py`** with agent-specific config:
   - Class name and docstring
   - Constructor fields (e.g., `rust_version`), listed in `_FIELDS` so the LLM does not get them as tools
   - `_CONTEXT_FILES` (e.g., `("RUSTY.md",)` — agent-specific file; shared files like `AGENTS.md` are read automatically)
   - `_CLASS_NAME` (e.g., `"Rusty"`)
   - `_ALLOWED_ROUTER_KEYS` for `develop-github-issue` routing
   - `_mcp_servers()` returning agent-specific MCP services
   - `_load_prompt()` pointing to `src/rusty/prompts/`
   - Thin wrapper `@function` methods delegating to `agent_base`, file tools taking `ws: dagger.Workspace`, and an `@agent` function for `dagger agent`

   See [`angie/src/angie/main.py`](angie/src/angie/main.py) for a complete example.

6. **Add prompts** in `rusty/src/rusty/prompts/` (system, assist, review, build, upgrade, router, task_system, suggest_fix, write_tests). Prompts describe their inputs under `## Inputs`; the values are appended under `## Input values`, and the result is the final reply.

7. **Run `dagger generate -y`** and commit the generated `sdk/`, `clients/` and `uv.lock`. The Daggerverse description comes from the docstring of `src/rusty/__init__.py`.

8. **Add tests** following the `.agent-tests` convention.

## Roadmap

This project is under active development. Here's what's coming next:

- [ ] Expand `gcp-vertex-ai` module (Vertex AI Agent Engine)
- [ ] Add `gcp-cloud-storage` module (bucket management, object operations)
- [ ] Add `gcp-kubernetes-engine` module (GKE cluster and workload management)
- [ ] Add `gcp-cloud-sql` module (instance provisioning, database management)
- [ ] Add `gitlab-issue` module (GitLab issue integration for AI agents)
- [ ] Add `jira-issue` module (Jira issue integration for AI agents)
- [ ] Add `develop-gitlab-issue` and `develop-jira-issue` entrypoints to Angie, Monty, and Goose
- [ ] Add Scaleway modules

Have a feature request? [Open an issue](https://github.com/telchak/daggerverse/issues)!

## Sponsoring

Every CI run exercises real infrastructure — GitHub Actions runners, GCP services (Cloud Run, Firebase, Artifact Registry, Vertex AI), and LLM API calls (Gemini) for the AI agent tests. If you find these modules useful, consider [sponsoring the project](https://github.com/sponsors/telchak) to help cover these ongoing costs.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.
