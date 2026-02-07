# gcp-orchestrator-agent

AI-powered multi-service GCP deployment and troubleshooting agent using the Dagger LLM API. Supports Cloud Run, Firebase Hosting, Vertex AI, and health checks.

## Installation

```shell
dagger install github.com/certainty-labs/daggerverse/gcp-orchestrator-agent@<version>
```

## Features

- **Multi-service deployment**: Cloud Run, Firebase Hosting, Vertex AI
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

### Cloud Run

```shell
dagger call deploy \
  --gcloud=<authenticated-container> \
  --project-id=my-project \
  --service-name=my-service \
  --assignment="Deploy gcr.io/google-samples/hello-app:1.0, allow unauthenticated access"
```

### Firebase Hosting

```shell
dagger call deploy \
  --gcloud=<authenticated-container> \
  --project-id=my-project \
  --credentials=file:./service-account.json \
  --service-name=my-site \
  --source=. \
  --assignment="Deploy to Firebase Hosting"
```

### Vertex AI

```shell
dagger call deploy \
  --gcloud=<authenticated-container> \
  --project-id=my-project \
  --service-name=my-model \
  --assignment="Deploy my-model container to Vertex AI with n1-standard-4 machine type"
```

### Troubleshooting

```shell
dagger call troubleshoot \
  --gcloud=<authenticated-container> \
  --project-id=my-project \
  --service-name=my-service \
  --issue="Service returns 503 errors intermittently"
```

## DAGGER.md

Create a `DAGGER.md` file in your repository root to give the agent per-repo context:

```markdown
# Deployment Context

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

## GCP Documentation Search (Optional)

The agent can search Google's official developer documentation in real time during deployments and troubleshooting. This gives it access to the latest GCP docs for Firebase, Cloud Run, Vertex AI, Android, Maps, and more.

### Setup

1. Enable the Developer Knowledge API in your GCP project:
   ```shell
   gcloud services enable developerknowledge.googleapis.com --project=PROJECT_ID
   ```

2. Create an API key restricted to the Developer Knowledge API:
   ```shell
   gcloud services api-keys create --project=PROJECT_ID --display-name="DK API Key"
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

## Authentication

This module requires an authenticated `gcloud` container (via `gcp-auth` module). For Firebase operations, also provide `--credentials` (service account JSON key).

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
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

#### Using OpenAI (GPT)

```shell
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4-turbo"  # optional

dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

#### Using Google Gemini

```shell
export GEMINI_API_KEY="your-api-key"
export GEMINI_MODEL="gemini-1.5-pro"  # optional

dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

#### Using Local Models (Docker Model Runner / Ollama)

```shell
export OPENAI_BASE_URL="http://model-runner.docker.internal/engines/v1/"
export OPENAI_MODEL="index.docker.io/ai/qwen2.5:7B-F16"
export OPENAI_DISABLE_STREAMING="true"

dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

Dagger will automatically detect which provider to use based on the environment variables set. You can also use a `.env` file in the current directory.

## Migration from gcp-cloud-run-agent

If you were using `gcp-cloud-run-agent`, update your references:

| Before | After |
|--------|-------|
| `gcp-cloud-run-agent` | `gcp-orchestrator-agent` |
| `dag.gcp_cloud_run_agent()` | `dag.gcp_orchestrator_agent()` |
| `cloud-run-tools` | `orchestrator-tools` |
| `CloudRunTools` | `OrchestratorTools` |

The `deploy` and `troubleshoot` entrypoints have the same signatures, with the addition of optional `credentials` (for Firebase) on the constructor and optional `source` on `troubleshoot` (for DAGGER.md context).

## Dependencies

- [gcp-cloud-run](../gcp-cloud-run) - Cloud Run service/job operations
- [gcp-artifact-registry](../gcp-artifact-registry) - Container image publishing
- [gcp-firebase](../gcp-firebase) - Firebase Hosting deployment
- [gcp-vertex-ai](../gcp-vertex-ai) - Vertex AI model deployment
- [health-check](../health-check) - Container health checking
