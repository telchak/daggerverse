# Daggerverse - Reusable Dagger Modules

A collection of small, independent, reusable Dagger modules for CI/CD pipelines.

## Available Modules

| Module | Description | Dependencies |
|--------|-------------|--------------|
| **calver** | Calendar Versioning utilities | None |
| **gcp-auth** | GCP authentication utilities | None |
| **gcp-artifact-registry** | Artifact Registry operations | gcp-auth |
| **gcp-cloud-run** | Cloud Run deployment | gcp-auth |
| **gcp-vertex-ai** | Vertex AI model deployment | gcp-auth |
| **gcp-firebase** | Firebase Hosting deployment | None |
| **health-check** | Container health checking | None |
| **oidc** | OIDC token utilities | None |

## Installation

Install modules with a specific version:

```bash
dagger install github.com/YOUR_ORG/daggerverse/calver@v1.0.0
dagger install github.com/YOUR_ORG/daggerverse/gcp-auth@v1.0.0
```

Or use the latest from main (not recommended for production):

```bash
dagger install github.com/YOUR_ORG/daggerverse/calver
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
├── health-check/
├── oidc/                # OIDC token utilities
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
# Tests without credentials
dagger -m tests call calver
dagger -m tests call health-check

# GCP tests (require credentials)
dagger -m tests call gcp-auth \
  --workload-identity-provider="..." \
  --service-account="..." \
  --project-id="..." \
  --oidc-token=env:TOKEN \
  --oidc-url=env:URL
```

### Test Coverage

| Test | Credentials Required |
|------|---------------------|
| `calver` | No |
| `health-check` | No |
| `gcp-auth` | Yes (OIDC) |
| `gcp-artifact-registry` | Yes (OIDC) |
| `gcp-cloud-run` | Yes (OIDC) |
| `gcp-vertex-ai` | Yes (OIDC) |
| `gcp-firebase` | No (build only) |

### CI

Tests run automatically on push/PR via GitHub Actions. GCP tests use Workload Identity Federation for keyless authentication.

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

## Module Guidelines

### Design Principles

- Keep modules small and focused
- Single responsibility per module
- Use `Doc` annotations for parameters

### Naming Conventions

- **Modules**: `kebab-case` (e.g., `gcp-auth`)
- **Functions**: `snake_case` (e.g., `verify_credentials`)
- **Parameters**: `snake_case` (e.g., `project_id`)

## Dependency Graph

```
gcp-auth (base)
├── gcp-artifact-registry
├── gcp-cloud-run
└── gcp-vertex-ai

calver (independent)
health-check (independent)
gcp-firebase (independent)
oidc (independent)
```

## Publishing

Modules are versioned independently using semantic versioning (`vMAJOR.MINOR.PATCH`).

### Version Tags

Each module has its own version tags prefixed with the module name:

```
calver/v1.0.0
gcp-auth/v1.2.3
health-check/v0.5.0
```

### Publishing a Module

Use the **Publish Module** workflow in GitHub Actions:

1. Go to Actions > Publish Module
2. Select the module to publish
3. Choose version bump type (major/minor/patch)
4. Run the workflow

The workflow will:
- Calculate the next version from existing tags
- Validate the module loads correctly
- Create and push the version tag
- Create a GitHub Release

### Manual Tagging

```bash
# Create a version tag
git tag -a calver/v1.0.0 -m "Release calver v1.0.0"
git push origin calver/v1.0.0
```

## Contributing

1. Follow the established patterns
2. Keep modules small and focused
3. Add tests to the `tests/` module
4. Update documentation

## License

Apache 2.0
