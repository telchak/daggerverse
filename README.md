# Daggerverse - Reusable Dagger Modules

[![CI](https://github.com/telchak/daggerverse/actions/workflows/ci.yml/badge.svg)](https://github.com/telchak/daggerverse/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Dagger](https://img.shields.io/badge/Dagger-v0.19.11-1a1a2e.svg)](https://dagger.io)

A collection of small, independent, reusable [Dagger](https://github.com/dagger/dagger) modules for CI/CD pipelines. Built with the [Dagger SDK](https://docs.dagger.io) and published on the [Daggerverse](https://daggerverse.dev).

## Available Modules

| Module | Description |
|--------|-------------|
| [**calver**](calver/) | Calendar Versioning utilities |
| [**gcp-auth**](gcp-auth/) | GCP authentication (OIDC, Workload Identity Federation, Service Account) |
| [**gcp-artifact-registry**](gcp-artifact-registry/) | Artifact Registry container image operations |
| [**gcp-cloud-run**](gcp-cloud-run/) | Cloud Run service and job deployment |
| [**gcp-vertex-ai**](gcp-vertex-ai/) | Vertex AI model deployment |
| [**gcp-firebase**](gcp-firebase/) | Firebase Hosting deployment and preview channels |
| [**gcp-orchestrator-agent**](gcp-orchestrator-agent/) | AI-powered multi-service GCP deployment and troubleshooting agent |
| [**health-check**](health-check/) | HTTP and TCP container health checking |
| [**oidc-token**](oidc-token/) | OIDC token exchange utilities |
| [**semver**](semver/) | Semantic Versioning with Conventional Commits |

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

## Architecture

```
daggerverse/
├── calver/              # Calendar versioning
├── gcp-auth/            # GCP authentication (base)
├── gcp-artifact-registry/
├── gcp-cloud-run/
├── gcp-vertex-ai/
├── gcp-firebase/
├── gcp-orchestrator-agent/  # AI agent (Cloud Run, Firebase, Vertex AI)
├── health-check/
├── oidc-token/          # OIDC token utilities
├── semver/              # Semantic versioning
└── tests/               # Centralized test suite
```

## Quick Start

### CalVer - Generate versions

```bash
# Generate date-based version
dagger -m calver call generate --format="YYYY.0M.0D"
# Output: 2025.12.14

# Auto-increment from git tags
dagger -m calver call generate --source=. --format="v.YYYY.MM.MICRO"
# Output: v.2025.12.3
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

Tests run automatically on push/PR via GitHub Actions:
- `test-basic`: calver, health-check, oidc-token, semver
- `test-gcp`: All GCP modules with shared OIDC authentication

### Validation Pipeline

| Check | Type | Description |
|-------|------|-------------|
| dagger.json exists | Error | Required for all modules |
| dagger.json has description | Error | Required for discoverability |
| README.md exists | Error | Required documentation |
| examples/ directory exists | Error | Required for usage examples |
| Line count < 300 | Warning | Keep modules small |
| Function docstrings | Warning | All public functions documented |
| Emojis in code | Warning | Avoid emojis for clean output |
| Module loads | Error | Validates module syntax |
| Example modules load | Error | Validates examples work |

## Architecture

Modules are designed to be independent, with one exception: `gcp-auth` depends on `oidc-token` for GitHub Actions OIDC token exchange. GCP modules accept pre-authenticated containers from `gcp-auth`:

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
v2026.2.0   ← first release of February 2026
v2026.2.1   ← second release of February 2026
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

## Roadmap

This project is under active development. Here's what's coming next:

- [ ] Expand `gcp-vertex-ai` module (Vertex AI Agent Engine)
- [ ] Add `gcp-cloud-storage` module (bucket management, object operations)
- [ ] Add `gcp-kubernetes-engine` module (GKE cluster and workload management)
- [ ] Add `gcp-cloud-sql` module (instance provisioning, database management)
- [ ] Add GCP developer agents (specialized AI agents for GCP workflows)
- [ ] Add Scaleway modules

Have a feature request? [Open an issue](https://github.com/telchak/daggerverse/issues)!

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.
