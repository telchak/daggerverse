# gcp-orchestrator-agent

AI-powered multi-service GCP deployment and troubleshooting agent using the Dagger LLM API. Supports Cloud Run, Firebase Hosting, Vertex AI, and health checks.

## Installation

```shell
dagger install github.com/certainty-labs/daggerverse/gcp-orchestrator-agent@<version>
```

## Features

- **Multi-service deployment**: Cloud Run, Firebase Hosting, Vertex AI
- **Simplified auth**: One set of credentials for gcloud + Firebase (no separate `--firebase-*` flags)
- **Auto-discovery**: project_id and region extracted from gcloud config when omitted
- **Optional service_name**: LLM reads from DAGGER.md or assignment when not provided
- **DAGGER.md support**: Per-repo context files that customize agent behavior
- **GCP docs search**: Optional real-time search of Google's official developer documentation
- **Health checks**: HTTP and TCP health verification for containers
- **Troubleshooting**: AI-powered diagnostics across all supported services
- **One agent, any repo**: Same module reference works across all repositories

## Functions

| Function | Description |
|----------|-------------|
| `deploy` | Deploy a service using an AI agent (Cloud Run, Firebase, or Vertex AI) |
| `troubleshoot` | Troubleshoot a GCP service using an AI agent |

## Quick Start

### Option 1: OIDC / Workload Identity Federation (recommended for CI/CD)

```shell
dagger call deploy \
  --oidc-token=env:OIDC_TOKEN \
  --workload-identity-provider="projects/PROJECT_NUM/locations/global/workloadIdentityPools/POOL/providers/PROVIDER" \
  --service-account-email="sa@project.iam.gserviceaccount.com" \
  --project-id=my-project \
  --source=. \
  --assignment="Deploy to Cloud Run, allow unauthenticated access"
```

### Option 2: Service Account JSON key

```shell
dagger call deploy \
  --credentials=file:./service-account.json \
  --source=. \
  --assignment="Deploy to Firebase Hosting"
```

project_id is auto-extracted from the SA JSON key.

### Option 3: Host gcloud config (local development)

```shell
dagger call deploy \
  --google-cloud-dir ~/.config/gcloud \
  --source=. \
  --assignment="Deploy to Cloud Run, allow unauthenticated access"
```

Uses your local `gcloud auth login` session. project_id and region are auto-discovered from your gcloud config. Requires `gcloud auth login` and optionally `gcloud auth application-default login` to have been run on your machine.

### Option 4: Pre-built gcloud container (backward compatible)

```shell
dagger call deploy \
  --gcloud=<authenticated-container> \
  --project-id=my-project \
  --service-name=my-service \
  --assignment="Deploy gcr.io/google-samples/hello-app:1.0, allow unauthenticated access"
```

### Troubleshooting

```shell
dagger call troubleshoot \
  --oidc-token=env:OIDC_TOKEN \
  --workload-identity-provider="projects/PROJECT_NUM/locations/global/..." \
  --project-id=my-project \
  --service-name=my-service \
  --issue="Service returns 503 errors intermittently"
```

## Authentication

The agent supports four authentication paths. For OIDC and SA JSON, one set of credentials is used for both gcloud operations (Cloud Run, Artifact Registry, Vertex AI) and Firebase Hosting.

| Scenario | Flags needed |
|----------|-------------|
| OIDC/WIF (CI/CD) | `--oidc-token` + `--workload-identity-provider` + `--project-id` |
| SA JSON key | `--credentials` (project_id auto-extracted) |
| Host gcloud (local dev) | `--google-cloud-dir ~/.config/gcloud` (project_id/region auto-discovered) |
| Pre-built gcloud | `--gcloud` + `--project-id` (+ `--oidc-token`/`--credentials` if Firebase needed) |

### Auto-discovery

- **project_id**: Auto-extracted from SA JSON credentials, or read from `gcloud config get-value project` when using host gcloud config or a pre-built gcloud container
- **region**: Read from `gcloud config get-value compute/region`, defaults to `us-central1`
- **service_name**: Optional — LLM determines it from DAGGER.md or the assignment/issue text

### Migration from previous versions

| Old flag | New flag |
|----------|----------|
| `--firebase-oidc-token` | `--oidc-token` |
| `--firebase-workload-identity-provider` | `--workload-identity-provider` |
| `--firebase-service-account-email` | `--service-account-email` |
| `--service-name` (required) | `--service-name` (optional) |
| `--gcloud` (required) | `--gcloud` (optional, one of four auth paths) |
| *(not available)* | `--google-cloud-dir` (new, for local dev) |

## DAGGER.md

Create a `DAGGER.md` file in your repository root to give the agent per-repo context:

```markdown
# Deployment Context

## Project
- Project ID: my-project
- Region: us-central1
- Service name: my-api

## Service Type
Cloud Run

## Build
- Framework: FastAPI
- Port: 8080
- Build command: `docker build -t app .`

## Deployment Preferences
- Memory: 1Gi
- CPU: 1
- Min instances: 0
- Allow unauthenticated: true
- Environment: ENV=production
```

When `--source` is provided and contains a `DAGGER.md`, the agent reads it and uses the context to make better deployment decisions.

### Parsed fields

The agent automatically extracts these key-value fields from DAGGER.md (using `Key: value` format):

| Field | DAGGER.md key | Example |
|-------|--------------|---------|
| project_id | `Project ID:` or `project_id:` | `my-project` |
| region | `Region:` | `us-central1` |
| service_name | `Service name:` or `service_name:` | `my-api` |

### Configuration priority order

All values follow: **explicit CLI flags > DAGGER.md > gcloud config > defaults**

For example, if DAGGER.md says `Region: europe-west1` but you pass `--region us-central1`, the CLI flag wins.

## GCP Documentation Search (Optional)

The agent can search Google's official developer documentation in real time during deployments and troubleshooting, using the [Developer Knowledge API](https://developers.google.com/knowledge/api) ([announcement blog post](https://developers.googleblog.com/introducing-the-developer-knowledge-api-and-mcp-server/)). This gives it access to the latest GCP docs for Firebase, Cloud Run, Vertex AI, Android, Maps, and more.

### Setup

1. Enable the Developer Knowledge API in your GCP project:
   ```shell
   gcloud services enable developerknowledge.googleapis.com --project=PROJECT_ID
   ```

2. Create an API key restricted to the Developer Knowledge API:
   ```shell
   gcloud services api-keys create \
     --api-target=service=developerknowledge.googleapis.com \
     --display-name="DK API Key" \
     --project=PROJECT_ID
   ```

3. Pass the key when calling the agent:
   ```shell
   dagger call deploy \
     --developer-knowledge-api-key=env:DEVELOPERKNOWLEDGE_API_KEY \
     --assignment="..." \
     ...
   ```

When the API key is provided, three additional tools become available to the agent:
- `search_gcp_docs` — search documentation by query
- `get_gcp_doc` — retrieve full page content
- `batch_get_gcp_docs` — retrieve multiple pages at once

When the API key is not provided, these tools are simply not used. The agent works normally without them.

## LLM Configuration

This module uses the Dagger LLM API which supports multiple providers. Configure your preferred LLM by setting the appropriate environment variables for the Dagger engine.

### Supported LLM Providers

| Provider | Required Env Var | Model Env Var | Default Model |
|----------|------------------|---------------|---------------|
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` | `claude-sonnet-4-5` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` | `gpt-4o` |
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` | `gemini-2.0-flash` |

### Usage with Different Models

#### Using Anthropic (Claude)

```shell
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_MODEL="claude-opus-4-5-20251101"  # optional

dagger call deploy \
  --oidc-token=env:OIDC_TOKEN \
  --workload-identity-provider="projects/..." \
  --project-id=my-project \
  --assignment="Deploy my-image as a public service"
```

#### Using OpenAI (GPT)

```shell
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4-turbo"  # optional

dagger call deploy \
  --credentials=file:./sa.json \
  --assignment="Deploy my-image as a public service"
```

#### Using Local Models (Docker Model Runner / Ollama)

```shell
export OPENAI_BASE_URL="http://model-runner.docker.internal/engines/v1/"
export OPENAI_MODEL="index.docker.io/ai/qwen2.5:7B-F16"
export OPENAI_DISABLE_STREAMING="true"

dagger call deploy \
  --gcloud=<authenticated-container> \
  --project-id=my-project \
  --assignment="Deploy my-image as a public service"
```

Dagger will automatically detect which provider to use based on the environment variables set. You can also use a `.env` file in the current directory.

## Dependencies

- [gcp-auth](../gcp-auth) - GCP authentication (builds gcloud containers from raw credentials)
- [gcp-cloud-run](../gcp-cloud-run) - Cloud Run service/job operations
- [gcp-artifact-registry](../gcp-artifact-registry) - Container image publishing
- [gcp-firebase](../gcp-firebase) - Firebase Hosting deployment
- [gcp-vertex-ai](../gcp-vertex-ai) - Vertex AI model deployment
- [health-check](../health-check) - Container health checking
