# GCP Auth - Dagger Module

Authenticate to Google Cloud Platform from Dagger pipelines.

**Inspired by:** [`google-github-actions/auth`](https://github.com/google-github-actions/auth)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Authentication Methods](#authentication-methods)
- [Functions](#functions)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

This Dagger module provides utilities for authenticating with Google Cloud Platform in CI/CD pipelines. It supports multiple authentication methods and exports standard GCP environment variables.

### Key Features

✅ Service Account Key authentication
✅ **GitHub Actions OIDC** (Workload Identity Federation) - No keys needed!
✅ Automatic environment variable configuration
✅ Pre-configured gcloud SDK containers
✅ Credential validation
✅ Docker registry authentication
✅ Detailed documentation and examples

## 🎯 Features

### Authentication Methods

1. **GitHub Actions OIDC** - Recommended for GitHub Actions (no keys!)
2. **Service Account Key JSON** - For other CI/CD pipelines
3. **Application Default Credentials** - For local development

### Core Functions

| Function | Description |
|----------|-------------|
| `with-credentials` | Add GCP credentials to any container |
| `with-github-actions-oidc` | Add GitHub Actions OIDC credentials (WIF) |
| `gcloud-container` | Get authenticated gcloud SDK container (service account) |
| `gcloud-container-from-github-actions` | Get authenticated gcloud container (GitHub Actions OIDC) |
| `gcloud-container-from-host` | Get authenticated gcloud SDK container (ADC) |
| `verify-credentials` | Validate credentials before use |
| `get-project-id` | Extract project ID from credentials |
| `configure-docker-auth` | Set up Docker for Artifact Registry |

## 🚀 Quick Start

### Installation

From your Dagger module:

```bash
dagger install ../daggerverse/gcp-auth --name=gcp-auth
```

### Basic Usage

```python
from dagger import dag

# Get authenticated gcloud container
gcloud = dag.gcp_auth().gcloud_container(
    credentials=env:GOOGLE_CREDENTIALS,
    project_id="my-project",
    region="us-central1"
)

# Run gcloud commands
output = await gcloud.with_exec([
    "gcloud", "compute", "instances", "list"
]).stdout()
```

### Prerequisites

- **GCP Service Account** with appropriate IAM permissions
- **Service Account Key** (JSON format) stored as Dagger secret
- **Project ID** where resources will be accessed

## 🔐 Authentication Methods

### Method 1: GitHub Actions OIDC (Recommended for GitHub Actions)

**No service account keys needed!** This method uses Workload Identity Federation to authenticate directly from GitHub Actions.

**GCP Setup (one-time):**

```bash
# Set variables
PROJECT_ID="my-project"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"
SA_NAME="github-actions-sa"
REPO="owner/repo"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create $POOL_NAME \
    --location="global" \
    --display-name="GitHub Actions Pool"

# Create OIDC Provider
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"

# Create Service Account
gcloud iam service-accounts create $SA_NAME \
    --display-name="GitHub Actions Service Account"

# Grant SA permissions (example: Cloud Run deployer)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.developer"

# Allow GitHub Actions to impersonate the SA
gcloud iam service-accounts add-iam-policy-binding \
    $SA_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$REPO"
```

**GitHub Actions Usage:**

```yaml
name: Deploy
on: push

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # Required for OIDC
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Deploy with Dagger
        run: |
          dagger call gcloud-container-from-github-actions \
            --workload-identity-provider="projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider" \
            --project-id="my-project" \
            --oidc-request-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
            --oidc-request-url=env:ACTIONS_ID_TOKEN_REQUEST_URL \
            --service-account-email="github-actions-sa@my-project.iam.gserviceaccount.com" \
            with-exec --args="gcloud","run","deploy","my-service","--region=us-central1","--image=gcr.io/my-project/my-image"
```

**Benefits:**
- ✅ No service account keys to manage or rotate
- ✅ No secrets to store in GitHub
- ✅ Short-lived credentials (more secure)
- ✅ Fine-grained access control per repository/branch

---

### Using with the `oidc-token` Module (Multi-CI Support)

For maximum flexibility across CI providers, use the `oidc-token` module to get tokens:

```yaml
# GitHub Actions - using oidc-token module
- name: Deploy with Dagger
  run: |
    # Get OIDC token using the oidc-token module
    TOKEN=$(dagger call -m ../oidc-token github-token \
      --request-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
      --request-url=env:ACTIONS_ID_TOKEN_REQUEST_URL \
      --audience="//iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider")

    # Use token with gcp-auth
    echo "$TOKEN" | dagger call gcloud-container-from-oidc \
      --oidc-token=stdin \
      --workload-identity-provider="projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider" \
      --project-id="my-project" \
      with-exec --args="gcloud","version"
```

This approach works with any CI provider supported by the `oidc-token` module (GitHub, GitLab, CircleCI).

---

### Method 2: Service Account Key (Recommended for other CI/CD)

**Setup:**

```bash
# Create service account
gcloud iam service-accounts create dagger-ci \
    --display-name="Dagger CI/CD"

# Grant permissions
gcloud projects add-iam-policy-binding MY_PROJECT \
    --member="serviceAccount:dagger-ci@MY_PROJECT.iam.gserviceaccount.com" \
    --role="roles/compute.admin"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=dagger-ci@MY_PROJECT.iam.gserviceaccount.com

# Use as Dagger secret
export GOOGLE_CREDENTIALS=$(cat key.json)
```

**Usage:**

```python
# Authenticate using service account key
gcloud = dag.gcp_auth().gcloud_container(
    credentials=env:GOOGLE_CREDENTIALS,
    project_id="my-project"
)
```

**⚠️ Important:**
- Store keys securely (never commit to git)
- Rotate keys regularly (90 days recommended)
- Use minimal IAM permissions
- Delete unused keys

### Method 3: Application Default Credentials (Local Development)

**For local development**, use your own Google Cloud credentials without managing service account keys:

**Setup:**

```bash
# Authenticate with your Google account
gcloud auth application-default login

# This will open a browser and save credentials to:
# - Linux/macOS: ~/.config/gcloud/application_default_credentials.json
# - Windows: %APPDATA%\gcloud\application_default_credentials.json

# Set default project (optional)
gcloud config set project MY_PROJECT
```

**Usage in Dagger:**

```python
# Use Application Default Credentials from host
gcloud = dag.gcp_auth().gcloud_container_from_host(
    project_id="my-project"
)

# Credentials are automatically mounted from host's ~/.config/gcloud/
# No need to pass credentials parameter
```

**Benefits:**
- ✅ No service account key management
- ✅ Uses your own Google account permissions
- ✅ Automatic credential refresh
- ✅ Perfect for local development and testing

**⚠️ Important:**
- Only use for local development (not CI/CD)
- Requires `gcloud auth application-default login` on host
- Inherits your user account permissions
- Not suitable for production pipelines

## 📚 Functions

### `with-credentials`

Add GCP credentials to any container.

```python
authenticated = dag.gcp_auth().with_credentials(
    container=dag.container().from_("python:3.11"),
    credentials=env:GOOGLE_CREDENTIALS,
    credentials_path="/tmp/gcp-creds.json",  # Optional
    export_env_vars=True                      # Optional
)
```

**Parameters:**
- `container` - Container to configure
- `credentials` - GCP service account key (JSON)
- `credentials_path` - Where to store credentials (default: `/tmp/gcp-credentials.json`)
- `export_env_vars` - Export GCP environment variables (default: `true`)

**Environment Variables Exported:**
- `GOOGLE_APPLICATION_CREDENTIALS`
- `CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE`

---

### `with-github-actions-oidc`

Configure container with GitHub Actions OIDC (Workload Identity Federation).

```python
authenticated = dag.gcp_auth().with_github_actions_oidc(
    container=dag.container().from_("python:3.11"),
    workload_identity_provider="projects/123456/locations/global/workloadIdentityPools/pool/providers/github",
    oidc_request_token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN,
    oidc_request_url=env:ACTIONS_ID_TOKEN_REQUEST_URL,
    service_account_email="sa@project.iam.gserviceaccount.com"  # Optional
)
```

**Parameters:**
- `container` - Container to configure
- `workload_identity_provider` - Full WIF provider resource name
- `oidc_request_token` - GitHub's `ACTIONS_ID_TOKEN_REQUEST_TOKEN` (Secret)
- `oidc_request_url` - GitHub's `ACTIONS_ID_TOKEN_REQUEST_URL` (Secret)
- `service_account_email` - Service account to impersonate (optional)

---

### `gcloud-container-from-github-actions`

Get pre-authenticated gcloud SDK container using GitHub Actions OIDC.

```python
gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
    workload_identity_provider="projects/123456/locations/global/workloadIdentityPools/pool/providers/github",
    project_id="my-project",
    oidc_request_token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN,
    oidc_request_url=env:ACTIONS_ID_TOKEN_REQUEST_URL,
    service_account_email="sa@project.iam.gserviceaccount.com",  # Optional
    region="us-central1"                                          # Optional
)
```

**Parameters:**
- `workload_identity_provider` - Full WIF provider resource name
- `project_id` - GCP project ID
- `oidc_request_token` - GitHub's `ACTIONS_ID_TOKEN_REQUEST_TOKEN` (Secret)
- `oidc_request_url` - GitHub's `ACTIONS_ID_TOKEN_REQUEST_URL` (Secret)
- `service_account_email` - Service account to impersonate (optional)
- `region` - Default region (default: `us-central1`)
- `image` - Base image (default: `google/cloud-sdk:alpine`)

---

### `gcloud-container`

Get pre-authenticated gcloud SDK container.

```python
gcloud = dag.gcp_auth().gcloud_container(
    credentials=env:GOOGLE_CREDENTIALS,
    project_id="my-project",
    region="us-central1",                     # Optional
    image="google/cloud-sdk:alpine",          # Optional
    components=["kubectl", "beta"]            # Optional
)
```

**Parameters:**
- `credentials` - GCP service account key (JSON)
- `project_id` - GCP project ID
- `region` - Default region (default: `us-central1`)
- `image` - Base image (default: `google/cloud-sdk:alpine`)
- `components` - Additional gcloud components to install

**Image Variants:**
- `google/cloud-sdk:alpine` - Smallest (recommended)
- `google/cloud-sdk:slim` - Small, Debian-based
- `google/cloud-sdk:latest` - Full, all components
- `google/cloud-sdk:460.0.0-alpine` - Pinned version

**Common Components:**
- `kubectl` - Kubernetes CLI
- `beta` - Beta commands
- `gke-gcloud-auth-plugin` - GKE auth
- `terraform-tools` - Terraform integration

---

### `gcloud-container-from-host`

Get pre-authenticated gcloud SDK container using Application Default Credentials from host.

```python
# Use host's Application Default Credentials
gcloud = dag.gcp_auth().gcloud_container_from_host(
    project_id="my-project",
    region="us-central1"                      # Optional
)

# Run gcloud commands with your credentials
output = await gcloud.with_exec([
    "gcloud", "compute", "instances", "list"
]).stdout()
```

**Parameters:**
- `project_id` - GCP project ID (required)
- `region` - Default region (default: `us-central1`)
- `image` - Base image (default: `google/cloud-sdk:alpine`)
- `components` - Additional gcloud components to install
- `gcloud_config_path` - Custom path to gcloud config (auto-detected)

**Prerequisites:**
```bash
# On your host machine, authenticate once:
gcloud auth application-default login
```

**Benefits:**
- ✅ No service account key management
- ✅ Uses your own Google account
- ✅ Perfect for local development

**Limitations:**
- ⚠️ Only works on authenticated host
- ⚠️ Not suitable for CI/CD pipelines

---

### `verify-credentials`

Validate credentials before use.

```python
email = await dag.gcp_auth().verify_credentials(
    credentials=env:GOOGLE_CREDENTIALS
)
print(f"Authenticated as: {email}")
```

**Returns:** Service account email
**Raises:** Exception if invalid

---

### `get-project-id`

Extract project ID from credentials.

```python
project_id = await dag.gcp_auth().get_project_id(
    credentials=env:GOOGLE_CREDENTIALS
)
```

**Returns:** Project ID string
**Raises:** Exception if not found

---

### `configure-docker-auth`

Configure Docker authentication for Artifact Registry.

```python
docker_container = dag.gcp_auth().configure_docker_auth(
    container=dag.container().from_("docker:latest"),
    credentials=env:GOOGLE_CREDENTIALS,
    registries=["us-central1-docker.pkg.dev"]  # Optional
)
```

**Default Registries:**
- `us-central1-docker.pkg.dev`
- `gcr.io`
- `us.gcr.io`, `eu.gcr.io`, `asia.gcr.io`

## 📖 Code Examples

This module includes runnable examples in Python, Go, and TypeScript. See the `examples/` directory:

```bash
# Python examples
cd examples/python && dagger functions

# Go examples
cd examples/go && dagger functions

# TypeScript examples
cd examples/typescript && dagger functions
```

Each examples module demonstrates:
- Verifying service account credentials
- Using authenticated gcloud containers
- Using Application Default Credentials
- Extracting project IDs
- Adding credentials to custom containers
- Installing gcloud components

## 💡 Usage Examples

### Example 1: Basic Authentication

```python
from dagger import dag, function, object_type

@object_type
class MyPipeline:
    @function
    async def deploy(self):
        # Verify credentials first
        email = await dag.gcp_auth().verify_credentials(
            credentials=env:GOOGLE_CREDENTIALS
        )
        print(f"✓ Authenticated as: {email}")

        # Get authenticated container
        gcloud = dag.gcp_auth().gcloud_container(
            credentials=env:GOOGLE_CREDENTIALS,
            project_id="my-project"
        )

        # Run commands
        await gcloud.with_exec(["gcloud", "services", "list"]).sync()
```

### Example 2: Deploy to Cloud Run

```python
@function
async def deploy_cloud_run(
    self,
    source: dagger.Directory,
    service_name: str,
):
    # Build container
    container = source.docker_build(dockerfile="Dockerfile")

    # Get authenticated gcloud
    gcloud = dag.gcp_auth().gcloud_container(
        credentials=env:GOOGLE_CREDENTIALS,
        project_id="my-project",
        region="us-central1"
    )

    # Deploy to Cloud Run
    await gcloud.with_exec([
        "gcloud", "run", "deploy", service_name,
        "--source=.",
        "--region=us-central1"
    ]).sync()
```

### Example 3: GKE Deployment

```python
@function
async def deploy_to_gke(
    self,
    cluster_name: str,
    manifest: dagger.File,
):
    # Get gcloud with kubectl
    gcloud = dag.gcp_auth().gcloud_container(
        credentials=env:GOOGLE_CREDENTIALS,
        project_id="my-project",
        region="us-central1",
        components=["kubectl", "gke-gcloud-auth-plugin"]
    )

    # Get cluster credentials
    gcloud = gcloud.with_exec([
        "gcloud", "container", "clusters", "get-credentials",
        cluster_name, "--region=us-central1"
    ])

    # Apply Kubernetes manifest
    await gcloud.with_file("/tmp/manifest.yaml", manifest).with_exec([
        "kubectl", "apply", "-f", "/tmp/manifest.yaml"
    ]).sync()
```

### Example 4: Multi-Cloud with Docker

```python
@function
async def build_and_push(
    self,
    source: dagger.Directory,
    image_name: str,
):
    # Build image
    container = source.docker_build(dockerfile="Dockerfile")

    # Configure Docker auth
    docker = dag.gcp_auth().configure_docker_auth(
        container=dag.container().from_("docker:latest"),
        credentials=env:GOOGLE_CREDENTIALS
    )

    # Push to Artifact Registry
    await docker.with_exec([
        "docker", "push",
        f"us-central1-docker.pkg.dev/my-project/repo/{image_name}"
    ]).sync()
```

## ✅ Best Practices

### Security

1. **Never commit credentials**
   ```bash
   # Add to .gitignore
   *.json
   gha-creds-*.json
   key.json
   ```

2. **Use minimal IAM permissions**
   ```bash
   # Grant only specific roles needed
   gcloud projects add-iam-policy-binding PROJECT \
       --member="serviceAccount:SA@PROJECT.iam.gserviceaccount.com" \
       --role="roles/storage.objectViewer"  # Not roles/owner!
   ```

3. **Rotate keys regularly**
   ```bash
   # Every 90 days
   gcloud iam service-accounts keys delete KEY_ID \
       --iam-account=SA@PROJECT.iam.gserviceaccount.com
   ```

4. **Use Application Default Credentials for local development**
   - No service account key management
   - Uses your own account permissions
   - Automatic credential refresh
   - Better security for local testing

### Performance

1. **Pin image versions**
   ```python
   gcloud = dag.gcp_auth().gcloud_container(
       image="google/cloud-sdk:460.0.0-alpine"  # Not :latest
   )
   ```

2. **Use alpine variant**
   ```python
   image="google/cloud-sdk:alpine"  # ~300MB vs ~1.5GB
   ```

3. **Install only needed components**
   ```python
   components=["kubectl"]  # Not ["kubectl", "beta", "alpha", ...]
   ```

### Reliability

1. **Verify credentials at start**
   ```python
   email = await dag.gcp_auth().verify_credentials(credentials)
   ```

2. **Handle errors gracefully**
   ```python
   try:
       await gcloud.with_exec(["gcloud", "..."]).sync()
   except Exception as e:
       print(f"Deployment failed: {e}")
       # Cleanup, rollback, notify
   ```

3. **Use consistent configuration**
   ```python
   # Set region once, use everywhere
   region = "us-central1"
   gcloud = dag.gcp_auth().gcloud_container(..., region=region)
   ```

## 🐛 Troubleshooting

### Common Issues

#### 1. Invalid Credentials

**Error:** `Failed to authenticate: no active account found`

**Solution:**
```python
# Verify credentials first
email = await dag.gcp_auth().verify_credentials(credentials)
```

**Common causes:**
- Malformed JSON
- Expired key
- Revoked service account
- Wrong secret variable name

---

#### 2. Permission Denied

**Error:** `ERROR: (gcloud...) User [...] does not have permission`

**Solution:**
```bash
# Check current permissions
gcloud projects get-iam-policy PROJECT \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:SA@PROJECT.iam.gserviceaccount.com"

# Grant needed permission
gcloud projects add-iam-policy-binding PROJECT \
    --member="serviceAccount:SA@PROJECT.iam.gserviceaccount.com" \
    --role="roles/REQUIRED_ROLE"
```

---

#### 3. Project ID Not Found

**Error:** `No project_id found in credentials`

**Solution:**
```python
# Explicitly provide project_id
gcloud = dag.gcp_auth().gcloud_container(
    credentials=env:GOOGLE_CREDENTIALS,
    project_id="my-explicit-project-id"  # Don't rely on credentials
)
```

---

#### 4. gcloud Command Not Found

**Error:** `gcloud: command not found`

**Solution:**
```python
# Use gcloud_container() instead of with_credentials()
gcloud = dag.gcp_auth().gcloud_container(...)  # Has gcloud pre-installed
```

---

### Debug Mode

Enable verbose output:

```python
gcloud = gcloud.with_env_variable("CLOUDSDK_CORE_VERBOSITY", "debug")
```

Check authentication:

```python
output = await gcloud.with_exec([
    "gcloud", "auth", "list"
]).stdout()
print(output)
```

## 📖 Related Resources

- **GitHub Actions Equivalent:** [google-github-actions/auth](https://github.com/google-github-actions/auth)
- **GCP Documentation:** [Service Account Keys](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)
- **Application Default Credentials:** [ADC Documentation](https://cloud.google.com/docs/authentication/application-default-credentials)
- **Dagger Documentation:** [Secrets](https://docs.dagger.io/api/secrets)
- **Best Practices:** [IAM Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)

## 🤝 Contributing

Improvements welcome! Common additions:
- Additional authentication methods
- More helper functions
- Better error messages
- Additional examples

## 📝 License

Same as parent project.
