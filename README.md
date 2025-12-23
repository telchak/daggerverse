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
│   └── examples/        # Python, Go examples
├── gcp-auth/            # GCP authentication (base)
│   └── examples/        # Python, Go, TypeScript examples
├── gcp-artifact-registry/
│   └── examples/
├── gcp-cloud-run/
│   └── examples/
├── gcp-vertex-ai/
│   └── examples/
├── gcp-firebase/
│   └── examples/
└── health-check/
    └── examples/
```

Each module includes built-in `test-all` and individual test functions.

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

## Running Tests

Each module includes `test-all` and individual test functions:

```bash
# From daggerverse/ directory

# Test calver (no credentials needed)
dagger -m calver call test-all

# Test health-check (no credentials needed)
dagger -m health-check call test-all

# Test GCP modules (requires credentials)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
dagger -m gcp-auth call test-all \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project
```

## Module Guidelines

### Design Principles

- Keep modules under 200 lines
- Single responsibility per module
- Use `Doc` annotations for parameters
- Provide examples for each module
- Include tests with an `all()` function

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
3. Add examples and tests
4. Update documentation

## License

Apache 2.0
