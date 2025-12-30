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

## Installation

Install modules from GitHub:

```bash
dagger install github.com/YOUR_ORG/daggerverse/MODULE_NAME
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
```

## Contributing

1. Follow the established patterns
2. Keep modules small and focused
3. Add tests to the `tests/` module
4. Update documentation

## License

Apache 2.0
