# Daggerverse - Reusable Dagger Modules

A collection of small, independent, reusable Dagger modules for CI/CD pipelines.

## Available Modules

| Module | Description |
|--------|-------------|
| **calver** | Calendar Versioning utilities |
| **gcp-auth** | GCP authentication utilities |
| **gcp-artifact-registry** | Artifact Registry operations |
| **gcp-cloud-run** | Cloud Run deployment |
| **gcp-vertex-ai** | Vertex AI model deployment |
| **gcp-firebase** | Firebase Hosting & Firestore |
| **health-check** | Container health checking |
| **oidc-token** | OIDC token utilities |
| **semver** | Semantic Versioning with Conventional Commits |

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

## Module Guidelines

### Design Principles

- Keep modules small and focused
- Single responsibility per module
- Use `Doc` annotations for parameters

### Naming Conventions

- **Modules**: `kebab-case` (e.g., `gcp-auth`)
- **Functions**: `snake_case` (e.g., `verify_credentials`)
- **Parameters**: `snake_case` (e.g., `project_id`)

## Architecture

All modules are independent and don't depend on each other. GCP modules accept pre-authenticated containers from `gcp-auth`:

```
gcp-auth ─────────────────────────────────────┐
  │ provides authenticated gcloud containers  │
  ├──> gcp-artifact-registry                  │
  ├──> gcp-cloud-run                          │
  ├──> gcp-vertex-ai                          │
  └──> gcp-firebase (firestore)               │
                                              │
gcp-firebase (hosting) <── access_token ──────┘

calver, health-check, oidc-token, semver (standalone)
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

### Automatic Releases

The **Release Modules** workflow runs on every push to main and:
- Detects which modules have changes since their last tag
- Analyzes commit messages using [Conventional Commits](https://www.conventionalcommits.org/)
- Automatically determines version bump (major/minor/patch)
- Creates tags and GitHub releases for changed modules

Commit message format:

| Commit Type | Version Bump |
|-------------|--------------|
| `feat:` | Minor |
| `fix:`, `perf:`, `refactor:` | Patch |
| `feat!:` or `BREAKING CHANGE:` | Major |

### Manual Publishing

Use the **Publish Module** workflow for manual releases:

1. Go to Actions > Publish Module
2. Select the module to publish
3. Choose version bump type (major/minor/patch)
4. Run the workflow

### Manual Tagging

```bash
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
