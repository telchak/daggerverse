# GCP Firebase - Dagger Module

Firebase Hosting and Firestore database management utilities for Dagger pipelines.

**No external dependencies** - This module is fully self-contained and authentication-agnostic.

## Installation

```bash
dagger install github.com/telchak/daggerverse/gcp-firebase
```

## Features

- **Firebase Hosting**: Build and deploy web applications, preview channels
- **Firestore**: Create, update, delete, and manage Firestore databases
- **Scripts**: Run Node.js, Python, or custom scripts with GCP credentials

---

## Authentication

This module supports three authentication methods. Choose based on your use case:

| Method | Best For | Security |
|--------|----------|----------|
| **OIDC + WIF** | CI/CD pipelines | Highest (no long-lived keys) |
| **Service Account** | Local development, simple setups | Medium (requires key management) |
| **Access Token** | Legacy/migration | Low (tokens expire quickly) |

### Option A: Service Account Credentials (JSON Key)

Use when you have a service account JSON key file. The module mounts the credentials and sets `GOOGLE_APPLICATION_CREDENTIALS` automatically.

```python
# Deploy with service account credentials
await dag.gcp_firebase().deploy(
    project_id="my-project",
    source=source,
    credentials=credentials,  # Service account JSON as Secret
    build_command="npm run build",
)
```

```bash
# CLI usage
dagger call deploy \
  --project-id=my-project \
  --source=. \
  --credentials=env:GOOGLE_CREDENTIALS \
  --build-command="npm run build"
```

### Option B: OIDC Token + Workload Identity Federation (Recommended)

Use for CI/CD pipelines. No long-lived credentials needed - uses short-lived OIDC tokens from your CI provider.

**Step 1:** Fetch OIDC token from your CI provider using the `oidc-token` module:

```python
# GitHub Actions
oidc_token = dag.oidc_token().github_token(
    request_token=oidc_request_token,
    request_url=oidc_request_url,
    audience=f"//iam.googleapis.com/{workload_identity_provider}",
)

# GitLab CI
oidc_token = dag.oidc_token().gitlab_token(ci_job_jwt)

# CircleCI
oidc_token = dag.oidc_token().circleci_token(circle_oidc_token)
```

**Step 2:** Deploy with the OIDC token:

```python
await dag.gcp_firebase().deploy(
    project_id="my-project",
    source=source,
    oidc_token=oidc_token,
    workload_identity_provider="projects/123/locations/global/workloadIdentityPools/...",
    service_account_email="deployer@my-project.iam.gserviceaccount.com",  # Optional
    build_command="npm run build",
)
```

**Complete GitHub Actions Example:**

```python
# In your Dagger module
async def deploy_from_github(
    source: dagger.Directory,
    workload_identity_provider: str,
    project_id: str,
    oidc_request_token: dagger.Secret,
    oidc_request_url: dagger.Secret,
) -> str:
    # Fetch OIDC token with GCP audience
    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    oidc_token = dag.oidc_token().github_token(
        request_token=oidc_request_token,
        request_url=oidc_request_url,
        audience=audience,
    )

    # Deploy using the token
    return await dag.gcp_firebase().deploy(
        project_id=project_id,
        source=source,
        oidc_token=oidc_token,
        workload_identity_provider=workload_identity_provider,
        build_command="npm run build",
    )
```

**GitHub Actions workflow:**

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Firebase
        run: |
          dagger call deploy \
            --project-id=${{ secrets.PROJECT_ID }} \
            --source=. \
            --oidc-token=env:OIDC_TOKEN \
            --workload-identity-provider=${{ secrets.WIF_PROVIDER }}
        env:
          ACTIONS_ID_TOKEN_REQUEST_TOKEN: ${{ secrets.ACTIONS_ID_TOKEN_REQUEST_TOKEN }}
          ACTIONS_ID_TOKEN_REQUEST_URL: ${{ secrets.ACTIONS_ID_TOKEN_REQUEST_URL }}
```

### Option C: Access Token (Deprecated)

For backward compatibility. Access tokens expire quickly and require external refresh.

```python
await dag.gcp_firebase().deploy(
    project_id="my-project",
    source=source,
    access_token=access_token,  # Pre-fetched GCP access token
    build_command="npm run build",
)
```

---

## Caching

All hosting functions mount an npm cache volume by default (`dag.cache_volume("firebase-npm")`) to speed up repeated dependency installs and Firebase CLI setup. You can pass a custom cache volume to share across modules:

```python
# Share a single npm cache across gcp-firebase and angular
npm_cache = dag.cache_volume("my-shared-npm")

await dag.gcp_firebase().deploy(
    project_id="my-project",
    source=source,
    credentials=credentials,
    npm_cache=npm_cache,
)

dist = await dag.gcp_firebase().build(source=source, npm_cache=npm_cache)
```

```bash
# CLI: caching is automatic, no extra flags needed
dagger call build --source=.
```

---

## Firebase Hosting

### Functions

| Function | Description |
|----------|-------------|
| `build` | Build web application and return dist directory |
| `deploy` | Build and deploy to Firebase Hosting |
| `deploy-preview` | Deploy to a preview channel, returns preview URL |
| `delete-channel` | Delete a preview channel |

### Deploy to Production

```python
result = await dag.gcp_firebase().deploy(
    project_id="my-firebase-project",
    source=source_dir,
    credentials=credentials,  # or oidc_token + workload_identity_provider
    build_command="npm run build",
    deploy_functions=True,
    force=True,
)
```

### Deploy Preview Channel

```python
preview_url = await dag.gcp_firebase().deploy_preview(
    project_id="my-firebase-project",
    channel_id="pr-123",
    source=source_dir,
    credentials=credentials,
    build_command="npm run build",
    expires="7d",
)
print(f"Preview: {preview_url}")
```

### Delete Preview Channel

```python
await dag.gcp_firebase().delete_channel(
    project_id="my-firebase-project",
    channel_id="pr-123",
    credentials=credentials,
)
```

### CLI Examples

```bash
# Build only
dagger call build --source=. --build-command="npm run build"

# Deploy to production
dagger call deploy \
  --project-id=my-project \
  --source=. \
  --credentials=env:GOOGLE_CREDENTIALS \
  --build-command="npm run build"

# Deploy preview channel
dagger call deploy-preview \
  --project-id=my-project \
  --channel-id=pr-123 \
  --source=. \
  --credentials=env:GOOGLE_CREDENTIALS \
  --expires=7d
```

---

## Firebase Scripts

Run scripts that interact with Firebase/Firestore using GCP credentials. Useful for data seeding, migrations, and administrative tasks.

### Functions

| Function | Description |
|----------|-------------|
| `node` | Run Node.js or TypeScript scripts |
| `python` | Run Python scripts |
| `container` | Get a container with credentials for any language |

### Node.js / TypeScript

```python
result = await dag.gcp_firebase().scripts().node(
    source=source,
    script="src/seed-data.ts",
    credentials=credentials,
    working_dir="functions",
    install_command="npm ci",
)
```

### Python

```python
result = await dag.gcp_firebase().scripts().python(
    source=source,
    script="seed_data.py",
    credentials=credentials,
    install_command="pip install firebase-admin",
)
```

### Other Languages (Go, Ruby, Java, etc.)

```python
container = dag.gcp_firebase().scripts().container(
    source=source,
    base_image="golang:1.22-alpine",
    credentials=credentials,
)
result = await container.with_exec(["go", "run", "main.go"]).stdout()
```

### CLI Examples

```bash
# Run TypeScript script
dagger call scripts node \
  --source=. \
  --script="src/seed-data.ts" \
  --credentials=env:GOOGLE_CREDENTIALS \
  --working-dir="functions"

# Run Python script
dagger call scripts python \
  --source=. \
  --script="seed_data.py" \
  --credentials=env:GOOGLE_CREDENTIALS \
  --install-command="pip install firebase-admin"
```

---

## Firestore Database Management

Manage Firestore databases programmatically.

**Note:** Firestore functions require an authenticated gcloud container. Use the `gcp-auth` module to create one, or provide your own container with `gcloud` CLI configured.

See: https://firebase.google.com/docs/firestore/manage-databases

### Functions

| Function | Description |
|----------|-------------|
| `create` | Create a new Firestore database |
| `update` | Update database configuration |
| `delete` | Delete a Firestore database |
| `describe` | Get details of a database |
| `list` | List all databases in the project |
| `exists` | Check if a database exists |

### Usage

```python
firestore = dag.gcp_firebase().firestore()

# Create a database
await firestore.create(
    gcloud=gcloud_container,
    database_id="my-database",
    location="us-central1",
)

# Check if exists
exists = await firestore.exists(
    gcloud=gcloud_container,
    database_id="my-database",
)

# Update delete protection
await firestore.update(
    gcloud=gcloud_container,
    database_id="my-database",
    delete_protection=True,
)

# Delete (disable protection first)
await firestore.update(gcloud=gcloud_container, database_id="my-database", delete_protection=False)
await firestore.delete(gcloud=gcloud_container, database_id="my-database")
```

---

## Migration from v1.x

If upgrading from a version that used `gcp-auth` internally:

**Removed functions:**
- `deploy_from_github_actions()` - Use `deploy()` with OIDC token
- `deploy_preview_from_github_actions()` - Use `deploy_preview()` with OIDC token

**Before (v1.x):**
```python
await dag.gcp_firebase().deploy_from_github_actions(
    workload_identity_provider=wif,
    project_id=project_id,
    oidc_request_token=token,
    oidc_request_url=url,
    source=source,
)
```

**After (v2.x):**
```python
# Fetch token yourself using oidc-token module
oidc_token = dag.oidc_token().github_token(
    request_token=token,
    request_url=url,
    audience=f"//iam.googleapis.com/{wif}",
)

# Pass token to deploy
await dag.gcp_firebase().deploy(
    project_id=project_id,
    source=source,
    oidc_token=oidc_token,
    workload_identity_provider=wif,
)
```

---

## License

Apache 2.0
