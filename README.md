# Daggerverse - Reusable Dagger Modules

[![CI](https://github.com/telchak/daggerverse/actions/workflows/ci.yml/badge.svg)](https://github.com/telchak/daggerverse/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Dagger](https://img.shields.io/badge/Dagger-v0.20.0-1a1a2e.svg)](https://dagger.io)
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

### Shared Agent Base (`_agent_base/`)

Angie, Monty, and Daggie share a common Python package ([`_agent_base/`](_agent_base/)) that provides the duplicated logic:

| Module | Purpose |
|--------|---------|
| `constants` | Blocked entrypoints and destructive tool lists |
| `workspace` | `read_file`, `edit_file`, `write_file`, `glob`, `grep` implementations |
| `llm_helpers` | LLM builders, context file reader, task sub-agent builder |
| `github_tools` | `suggest-github-fix`, `develop-github-issue`, PR code comments |
| `routing` | Router response parsing and function dispatch |

Each agent's `main.py` is a thin wrapper (~350 lines) that defines only what's unique: class name, constructor fields, MCP servers, prompt path, context file priority, and entrypoint signatures. The shared package is included via Dagger's `include` field in `dagger.json` and installed as a local Python dependency.

### Shared patterns

All agents follow the same design:
- **Workspace tools** (`read_file`, `edit_file`, `write_file`, `glob`, `grep`) for interacting with source code
- **Context files** for per-repo configuration (e.g. `ANGIE.md`, `MONTY.md`, `GOOSE.md`)
- **GitHub integration** via `develop-github-issue` to read an issue, route it to the right entrypoint, and open a PR
- **Blocked functions** to prevent LLM recursion on entrypoints

### Self-Improvement

All agents support a `--self-improve` constructor flag that creates a learning loop: the agent updates context files with discoveries made during the session, so it gets smarter across iterations.

| Mode | Behavior |
|------|----------|
| `off` (default) | No change — current behavior |
| `write` | Agent updates context files in the returned workspace directory |
| `commit` | Agent updates context files and creates a git commit in the returned workspace directory |

```bash
# Monty learns about your project as it works
dagger -m monty call assist \
  --source . \
  --self-improve=write \
  --assignment "Add a FastAPI health endpoint"
```

The agent writes to **two** context files:
- **Agent-specific file** (e.g. `MONTY.md`) — language/framework patterns, stack-specific conventions, tool gotchas
- **Shared file** (`AGENTS.md`) — project architecture, cross-cutting conventions, CI/CD patterns, team preferences

This separation prevents agent-specific knowledge from polluting shared context. When Monty discovers a Python async pattern, it goes in `MONTY.md`. When it discovers the project's folder structure, it goes in `AGENTS.md`.

**Reading** merges both files: the agent reads its own file (e.g. `MONTY.md`) plus the shared file (`AGENTS.md`, with `AGENT.md` and `CLAUDE.md` as legacy fallbacks). This applies to all directory-returning entrypoints (`assist`, `build`, `write-tests`, `upgrade`, `debug`).

## Installation

Install modules with a specific version:

```bash
dagger install github.com/telchak/daggerverse/calver@v1.0.0
dagger install github.com/telchak/daggerverse/gcp-auth@v1.0.0
```

Or use the latest from main (not recommended for production):

```bash
dagger install github.com/telchak/daggerverse/calver
```

## Quick Start

### CalVer - Generate versions

```bash
# Generate date-based version
dagger -m calver call generate --format="YYYY.0M.0D"
# Output: 2026.02.11

# Auto-increment from git tags
dagger -m calver call generate --source=. --format="v.YYYY.MM.MICRO"
# Output: v.2026.2.3
```

### GCP Auth - Authenticate

```bash
# Verify credentials
dagger -m gcp-auth call verify-credentials \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS
```

### Health Check - Verify containers

```bash
# HTTP health check
dagger -m health-check call http \
  --container=FROM_BUILD \
  --port=8080 \
  --path=/health
```

### Goose - GCP operations

```bash
# Troubleshoot a Cloud Run service
dagger -m goose call troubleshoot \
  --google-cloud-dir ~/.config/gcloud \
  --issue "Service returning 503 errors"

# Deploy with an AI agent
dagger -m goose call deploy \
  --google-cloud-dir ~/.config/gcloud \
  --assignment "Deploy image us-docker.pkg.dev/my-project/repo/app:latest as my-service" \
  --source .
```

### Monty - Python development

```bash
# Review Python code
dagger -m monty call review --source .

# General assistance
dagger -m monty call assist \
  --source . \
  --assignment "Add a FastAPI endpoint with Pydantic validation"
```

### Daggie - Dagger CI development

```bash
# Create a Dagger module for your project
dagger -m daggie call assist \
  --source . \
  --assignment "Create a Dagger module for building and testing this project"

# Explain a Dagger concept
dagger -m daggie call explain \
  --question "How does caching work in Dagger?"

# Debug a pipeline error
dagger -m daggie call debug \
  --source . \
  --error-output "$(dagger call build 2>&1)"
```

### Angie - Angular development

```bash
# Review Angular code
dagger -m angie call review --source .

# Build an Angular project
dagger -m angie call build --source .
```

## Architecture

```
daggerverse/
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

_agent_base ──> Shared agent logic (workspace, GitHub, LLM, routing)
  ├──> angie (Angular development agent)
  │      ├──> angular (deterministic build, lint, test, serve)
  │      └──> Angular CLI MCP
  ├──> daggie (Dagger CI specialist agent)
  │      └──> dagger-mcp (Dagger engine introspection MCP)
  └──> monty (Python development agent)
         ├──> python-build (deterministic build, lint, test, typecheck)
         ├──> python-lft MCP (linting, formatting, testing)
         └──> pypi-query MCP (package intelligence)

angular, calver, dagger-mcp, health-check, oidc-token, python-build, semver (standalone)
```

## Testing

Tests are centralized in the `tests/` module. This keeps the main modules clean and tests the public API exactly as users would.

### Run Tests Locally

```bash
# Tests without credentials (calver, health-check, oidc-token, semver)
dagger -m tests call all-no-credentials

# All GCP tests (require OIDC credentials)
dagger -m tests call all-gcp \
  --workload-identity-provider="..." \
  --service-account="..." \
  --project-id="..." \
  --repository="..." \
  --oidc-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
  --oidc-url=env:ACTIONS_ID_TOKEN_REQUEST_URL
```

### CI

Tests run automatically on push to `main`, pull requests, and manual dispatch via GitHub Actions. The pipeline has 6 stages:

| Job | Description |
|-----|-------------|
| `discover` | Auto-detects all modules and agents (classifies by `src/*/prompts/`), reads `.agent-tests` for per-agent test lists |
| `validate` | Checks every module for required files (`dagger.json` with description, `README.md`, `examples/`), loads functions, warns on source files exceeding 600 lines |
| `test-modules` | Matrix job — tests each non-agent module in parallel. GCP modules (`gcp-*`) receive OIDC credentials automatically |
| `test-agents` | Matrix job — tests each agent entrypoint in parallel (e.g. `angie-assist`, `goose-deploy`). Agents with `.agent-gcp` marker receive OIDC credentials |
| `test-angie-github-issue` | Dedicated job for `develop-github-issue` end-to-end test (creates a PR, then cleans it up) |
| `release` | Runs on `main` only — tags changed modules with semver (via Conventional Commits) and creates a CalVer release |

### Validation Pipeline

| Check | Type | Description |
|-------|------|-------------|
| dagger.json exists | Error | Required for all modules |
| dagger.json has description | Error | Required for discoverability |
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

Additionally, a common **CalVer release** (`vYYYY.MM.MICRO`) is created on each push to main to reference the whole set of modules as a coherent version:

```
v2026.2.0   <- first release of February 2026
v2026.2.1   <- second release of February 2026
```

### Automatic Releases

The **Release Modules** workflow runs on every push to main and:
- Detects which modules have changes since their last tag
- Analyzes commit messages using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)
- Automatically determines version bump (major/minor/patch)
- Creates per-module semver tags and a common CalVer release

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

1. **Initialize the module:**
   ```bash
   cd daggerverse
   dagger init rusty --sdk python
   ```

2. **Add the shared base to `rusty/dagger.json`:**
   ```json
   {
     "name": "rusty",
     "description": "AI-powered Rust development agent with MCP integration",
     "include": ["../_agent_base"],
     "dependencies": [
       {
         "name": "github-issue",
         "source": "github.com/kpenfound/dag/github-issue@b316e472d3de5bb0e54fe3991be68dc85e33ef38"
       }
     ]
   }
   ```

3. **Add `agent-base` to `rusty/pyproject.toml`:**
   ```toml
   dependencies = ["dagger-io", "agent-base"]

   [tool.uv.sources]
   dagger-io = { path = "sdk", editable = true }
   agent-base = { path = "../_agent_base", editable = true }
   ```

4. **Write `rusty/src/rusty/main.py`** with agent-specific config:
   - Class name and docstring
   - Constructor fields (e.g., `rust_version`)
   - `_CONTEXT_FILES` (e.g., `("RUSTY.md",)` — agent-specific file; shared files like `AGENTS.md` are read automatically)
   - `_CLASS_NAME` (e.g., `"Rusty"`)
   - `_ALLOWED_ROUTER_KEYS` for `develop-github-issue` routing
   - `_mcp_servers()` returning agent-specific MCP services
   - `_load_prompt()` pointing to `src/rusty/prompts/`
   - Thin wrapper `@function` methods delegating to `agent_base`

   See [`angie/src/angie/main.py`](angie/src/angie/main.py) for a complete example.

5. **Add prompts** in `rusty/src/rusty/prompts/` (system, assist, review, build, upgrade, router, task_system, suggest_fix, write_tests).

6. **Run `dagger develop`** to generate the SDK and validate, then re-add the `description` field to `dagger.json` (Dagger strips it).

7. **Add tests** following the `.agent-tests` convention.

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
