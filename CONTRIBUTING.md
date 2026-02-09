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
2. Install [Dagger](https://docs.dagger.io/install) (v0.19.11+)
3. Pick an [open issue](https://github.com/telchak/daggerverse/issues) or propose a new one
4. Create a feature branch from `main`
5. Make your changes, add tests, and open a pull request

## Development Setup

### Prerequisites

- [Dagger CLI](https://docs.dagger.io/install) v0.19.11+
- Python 3.12+ (modules use the Dagger Python SDK)
- A container runtime (Docker Desktop, Podman, OrbStack, etc.)

### Verify your setup

```bash
dagger version
# dagger v0.19.11 ...
```

### Repository structure

```
daggerverse/
├── calver/                     # Calendar versioning
├── gcp-auth/                   # GCP authentication (base)
├── gcp-artifact-registry/      # Artifact Registry operations
├── gcp-cloud-run/              # Cloud Run service/job deployment
├── gcp-vertex-ai/              # Vertex AI model deployment
├── gcp-firebase/               # Firebase Hosting & Firestore
├── gcp-orchestrator-agent/     # AI agent (Cloud Run, Firebase, Vertex AI)
├── health-check/               # HTTP and TCP container health checks
├── oidc-token/                 # OIDC token exchange utilities
├── semver/                     # Semantic versioning with Conventional Commits
├── tests/                      # Centralized test suite
├── .github/workflows/ci.yml   # CI pipeline
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

gcp-orchestrator-agent ──> AI agent that orchestrates:
  ├──> gcp-cloud-run
  ├──> gcp-artifact-registry
  ├──> gcp-firebase
  ├──> gcp-vertex-ai
  └──> health-check

calver, health-check, oidc-token, semver (standalone)
```

## Adding a New Module

### 1. Initialize the module

```bash
dagger init --sdk=python --name=my-module my-module/
mkdir my-module/examples
```

### 2. Required files

| File | Required | Description |
|------|----------|-------------|
| `dagger.json` | Yes | Must include a `"description"` field |
| `README.md` | Yes | Documentation with usage examples |
| `examples/` | Yes | Directory with example code |
| `src/<module>/main.py` | Yes | Module implementation |

Example `dagger.json`:

```json
{
  "name": "my-module",
  "sdk": "python",
  "description": "Short description of what this module does"
}
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
```

### 4. CI auto-discovery

The CI workflow automatically discovers all modules with a `dagger.json` file. No workflow changes needed unless:

- **GCP modules**: Name your module `gcp-*` and OIDC credentials are automatically passed
- **Special arguments**: Add a case in `.github/workflows/ci.yml`

## Testing

Tests are centralized in the `tests/` module. This keeps the main modules clean and tests the public API exactly as users would.

### Run tests locally

```bash
# Tests that don't require credentials
dagger call -m tests all-no-credentials

# Individual module test
dagger call -m tests calver
dagger call -m tests health-check

# GCP module tests (require OIDC credentials from GitHub Actions)
dagger call -m tests gcp-auth \
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
| `discover` | Finds all modules with a `dagger.json` |
| `validate` | Checks required files and module structure |
| `test` | Runs each module's test suite (parallel matrix) |
| `release` | Tags changed modules on merge to `main` |

### Validation checks

Every module is validated against these rules:

| Check | Severity | Description |
|-------|----------|-------------|
| `dagger.json` exists | Error | Required for all modules |
| `dagger.json` has `description` | Error | Required for discoverability |
| `README.md` exists | Error | Required documentation |
| `examples/` directory exists | Error | Required for usage examples |
| Line count < 300 | Warning | Keep modules small |
| Function docstrings | Warning | All public functions documented |
| Module loads | Error | Validates module syntax |
| Example modules load | Error | Validates examples work |

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

1. Ensure your changes pass validation (`dagger.json`, `README.md`, `examples/` exist)
2. Add or update tests in the `tests/` module
3. Update the module's `README.md` if you changed public API
4. Use Conventional Commit messages

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
- **Independent** — modules should not depend on each other (except `gcp-auth` → `oidc-token`)
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
4. A common CalVer release is created (e.g., `v2026.2.0`)

You do **not** need to manually bump versions or create tags.

## Getting Help

- **Questions**: [Open a discussion](https://github.com/telchak/daggerverse/issues) or comment on an existing issue
- **Bugs**: [File an issue](https://github.com/telchak/daggerverse/issues/new) with steps to reproduce
- **Feature requests**: [Open an issue](https://github.com/telchak/daggerverse/issues/new) describing the use case
- **Dagger docs**: [docs.dagger.io](https://docs.dagger.io)
