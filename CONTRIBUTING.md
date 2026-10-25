# Contributing to Daggerverse

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Architecture](#architecture)
- [Adding a New Module](#adding-a-new-module)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Module Guidelines](#module-guidelines)
- [Releases](#releases)
- [Getting Help](#getting-help)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Please report unacceptable behavior by [opening an issue](https://github.com/telchak/daggerverse/issues).

## Getting Started

1. **Fork** the repository and clone your fork
2. Install [Dagger](https://docs.dagger.io/install) v1.0.0-beta.21, the version CI uses
3. Pick an [open issue](https://github.com/telchak/daggerverse/issues) or propose a new one
4. Create a feature branch from `main`
5. Make your changes, add tests, and open a pull request

## Development Setup

### Prerequisites

- [Dagger CLI](https://docs.dagger.io/install) v1.0.0-beta.21. The CLI starts an engine of its own version; keep it on the version in `DAGGER_VERSION` of `.github/workflows/ci.yml`
- Python 3.13+ (modules use the Dagger Python SDK)
- A container runtime (Docker Desktop, Podman, OrbStack, etc.)

### Verify your setup

```bash
dagger version
# dagger v1.0.0-beta.21 ...
```

### Repository structure

```
daggerverse/
├── dagger.toml                 # Workspace: one Python SDK scope per module, with its clients
├── dagger.lock                 # Pinned Git refs and images
├── _agent_base/                # Shared library included by the coding agents
├── angie/                      # AI agent: Angular
├── angular/                    # Angular build, lint, test, serve
├── calver/                     # Calendar versioning
├── dagger-mcp/                 # MCP server for Dagger engine introspection
├── daggie/                     # AI agent: Dagger CI
├── gcp-artifact-registry/      # Artifact Registry operations
├── gcp-auth/                   # GCP authentication (base)
├── gcp-cloud-run/              # Cloud Run service/job deployment
├── gcp-firebase/               # Firebase Hosting & Firestore
├── gcp-vertex-ai/              # Vertex AI model deployment
├── goose/                      # AI agent: GCP operations (Cloud Run, Firebase, Vertex AI)
├── health-check/               # HTTP and TCP container health checks
├── monty/                      # AI agent: Python
├── oidc-token/                 # OIDC token exchange utilities
├── python-build/               # Python build, lint, test, typecheck
├── semver/                     # Semantic versioning with Conventional Commits
├── speck/                      # AI agent: spec-driven development
├── tests/                      # Centralized test suite
├── .github/workflows/ci.yml    # CI pipeline
├── LICENSE                     # Apache 2.0
└── README.md
```

### Module dependency graph

```
oidc-token ──> gcp-auth
                 │ provides authenticated gcloud containers
                 ├──> gcp-artifact-registry
                 ├──> gcp-cloud-run
                 ├──> gcp-vertex-ai
                 └──> gcp-firebase (OIDC, service account, or access token)

goose ──> AI agent that orchestrates:
  ├──> gcp-auth, gcp-cloud-run, gcp-artifact-registry
  └──> gcp-firebase, gcp-vertex-ai, health-check

angie ──> angular    monty ──> python-build    daggie ──> dagger-mcp    speck
  (the coding agents include _agent_base; every agent uses github-issue)

angular, calver, dagger-mcp, health-check, oidc-token, python-build, semver (standalone)
```

A module's dependencies are the `clients` of its scope in `dagger.toml`.

## Adding a New Module

### 1. Initialize the module

From the repository root:

```bash
dagger module init python --name my-module --path my-module
mkdir my-module/examples
```

This registers a Python SDK scope for the module in `dagger.toml` and writes `my-module/dagger-module.toml`. To call other modules, list them as the scope's clients, then regenerate:

```toml
[sdks.python.scopes.my-module]
clients = ["./oidc-token"]
is-module = true
```

```bash
dagger generate -y
```

Run `dagger generate -y` again whenever you change a function signature or the module's clients: the generated entrypoint (`sdk/entrypoint/`) bakes in the module's types, and `dagger check` fails when it is stale.

### 2. Required files

| File | Required | Description |
|------|----------|-------------|
| `dagger-module.toml` | Yes | Module manifest, written by `dagger module init` |
| `src/<package>/__init__.py` | Yes | Its docstring is the description shown on the Daggerverse |
| `src/<package>/main.py` | Yes | Module implementation |
| `pyproject.toml`, `uv.lock` | Yes | Commit the lockfile: the module builds with `uv sync --locked` |
| `sdk/`, `clients/` | Yes | Generated by `dagger generate`; commit them |
| `README.md` | Yes | Documentation with usage examples |
| `examples/` | Yes | Directory with example code |

Start the docstring text on the line after the opening quotes:

```python
"""
Short description of what this module does.

Longer explanation.
"""

from .main import MyModule as MyModule
```

### 3. Add tests

Create `tests/src/tests/my_module.py`:

```python
from dagger import dag

async def test_my_module() -> str:
    """Test my-module functions."""
    results = []
    result = await dag.my_module().some_function()
    results.append(f"[OK] some_function returned {result}")
    return "\n".join(results)
```

Then register it in `tests/src/tests/main.py`:

```python
from .my_module import test_my_module

# In the Tests class:
@function
async def my_module(self) -> str:
    """Run my-module tests."""
    return await test_my_module()

# If the tests need no credentials, also expose them as a check
# (`dagger check -m ./tests`). A check takes no arguments and returns None.
@function
@check
async def check_my_module(self) -> None:
    """Check the my-module module."""
    print(await self.my_module())
```

Add `"./my-module"` to the `clients` of `[sdks.python.scopes.tests]` in `dagger.toml`, then run `dagger generate -y`.

### 4. CI auto-discovery

The CI workflow automatically discovers all modules with a `dagger-module.toml` file. No workflow changes needed unless:

- **GCP modules**: Name your module `gcp-*` and OIDC credentials are automatically passed
- **Special arguments**: Add a case in `.github/workflows/ci.yml`

## Testing

Tests are centralized in the `tests/` module. This keeps the main modules clean and tests the public API exactly as users would.

### Run tests locally

```bash
# Workspace check: the committed sdk/ and clients/ match `dagger generate`
dagger check

# Module tests that don't require credentials, as checks
dagger check -m ./tests --generated=false

# Tests that don't require credentials (calver, health-check, oidc-token)
dagger api call -m ./tests all-no-credentials

# Individual module test
dagger api call -m ./tests calver
dagger api call -m ./tests health-check

# GCP module tests (require OIDC credentials from GitHub Actions)
dagger api call -m ./tests gcp-auth \
  --workload-identity-provider="..." \
  --service-account="..." \
  --project-id="..." \
  --oidc-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
  --oidc-url=env:ACTIONS_ID_TOKEN_REQUEST_URL
```

### CI pipeline

Tests run automatically on every push and pull request:

| Job | What it does |
|-----|--------------|
| `discover` | Finds all modules (a `dagger-module.toml`) and agents (a `src/*/prompts/` directory) |
| `validate` | Checks required files and that each module loads |
| `check` | Runs `dagger check`: the committed generated code must match `dagger generate` |
| `test-modules` | Runs each module's test suite (parallel matrix) |
| `test-agents` | Runs each agent's entrypoint tests (parallel matrix) |
| `test-angie-github-issue` | End-to-end `develop-github-issue` test (opens a PR, then cleans it up) |
| `release` | Tags changed modules on merge to `main` |

### Validation checks

Every module is validated against these rules:

| Check | Severity | Description |
|-------|----------|-------------|
| `dagger-module.toml` exists | Error | Required for all modules |
| Package docstring | Error | `src/<package>/__init__.py` docstring, shown on the Daggerverse |
| `README.md` exists | Error | Required documentation |
| `examples/` directory exists | Error | Required for usage examples |
| Module loads | Error | `dagger api functions` must succeed |
| Line count < 600 | Warning | Keep source files small |

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary) for automatic version bumps.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types and version bumps

| Type | Version Bump | Example |
|------|--------------|---------|
| `feat:` | Minor | `feat(auth): add OIDC support` |
| `fix:` | Patch | `fix(cloud-run): handle timeout` |
| `perf:` | Patch | `perf(firebase): reduce deploy time` |
| `refactor:` | Patch | `refactor(auth): simplify token flow` |
| `docs:` | Patch | `docs(readme): update examples` |
| `test:` | Patch | `test(cloud-run): add CRUD tests` |
| `chore:` | Patch | `chore: update dependencies` |
| `ci:` | Patch | `ci: add validation step` |
| `feat!:` or `BREAKING CHANGE:` | **Major** | `feat!: remove deprecated API` |

### Scope

Use the module name as the scope when the change is specific to one module:

```
feat(gcp-firebase): add Firestore CRUD operations
fix(health-check): handle connection refused
```

## Pull Requests

### Before submitting

1. Ensure your changes pass validation (`dagger-module.toml`, package docstring, `README.md`, `examples/`)
2. Run `dagger generate -y`, commit the generated `sdk/`, `clients/` and `uv.lock`, and check that `dagger check` passes
3. Add or update tests in the `tests/` module
4. Update the module's `README.md` if you changed public API
5. Use Conventional Commit messages

### PR process

1. Create a branch from `main` (e.g., `feat/gcp-storage-module`)
2. Make your changes with clear, atomic commits
3. Push and open a pull request against `main`
4. CI will run validation and tests automatically
5. Address any review feedback
6. Once approved and merged, the release workflow handles versioning and tagging

### What makes a good PR

- **Focused**: One module or one concern per PR
- **Tested**: New functionality has corresponding tests
- **Documented**: Public functions have `Doc` annotations and the README is updated
- **Small**: Prefer multiple small PRs over one large one

## Module Guidelines

### Design principles

- **Small and focused** — single responsibility per module
- **Independent** — plain modules should not depend on each other (except `gcp-auth` → `oidc-token`); agents build on the modules they orchestrate
- **User-friendly** — use `Doc` annotations on all parameters
- **Testable** — design functions to be testable via the Dagger API

### Naming conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `kebab-case` | `gcp-auth`, `health-check` |
| Functions | `snake_case` | `verify_credentials`, `deploy_service` |
| Parameters | `snake_case` | `project_id`, `service_name` |

### GCP module conventions

GCP modules follow a consistent pattern:

- Accept a pre-authenticated `gcloud` container from `gcp-auth`
- Use `project_id` and `region` as standard parameters
- Support multiple auth methods where applicable (OIDC/WIF, service account, access token)
- Name modules with the `gcp-` prefix for automatic CI credential injection

## Releases

Releases are fully automated. When a PR is merged to `main`:

1. The CI workflow detects which modules changed since their last tag
2. Commit messages are analyzed to determine the version bump (major/minor/patch)
3. Per-module semver tags are created (e.g., `gcp-auth/v1.2.3`)

You do **not** need to manually bump versions or create tags.

## Getting Help

- **Questions**: [Open a discussion](https://github.com/telchak/daggerverse/issues) or comment on an existing issue
- **Bugs**: [File an issue](https://github.com/telchak/daggerverse/issues/new) with steps to reproduce
- **Feature requests**: [Open an issue](https://github.com/telchak/daggerverse/issues/new) describing the use case
- **Dagger docs**: [docs.dagger.io](https://docs.dagger.io)
