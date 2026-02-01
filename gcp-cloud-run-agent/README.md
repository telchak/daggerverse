# gcp-cloud-run-agent

AI-powered Cloud Run deployment and troubleshooting agent using the Dagger LLM API.

## Installation

```shell
dagger install github.com/certainty-labs/daggerverse/gcp-cloud-run-agent@<version>
```

## Functions

| Function | Description |
|----------|-------------|
| `deploy` | Deploy a service to Cloud Run using an AI agent |
| `troubleshoot` | Troubleshoot a Cloud Run service using an AI agent |

## Usage

### CLI

```shell
# Deploy a pre-built image
dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy gcr.io/google-samples/hello-app:1.0, allow unauthenticated access" \
  --project-id=my-project \
  --service-name=my-service \
  --region=us-central1

# Troubleshoot a service
dagger call troubleshoot \
  --gcloud=<authenticated-container> \
  --service-name=my-service \
  --issue="Service returns 503 errors intermittently" \
  --project-id=my-project \
  --region=us-central1
```

### Python

```python
import dagger
from dagger import dag

async def deploy_with_agent():
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider="...",
        project_id="my-project",
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email="...",
    )

    result = await dag.gcp_cloud_run_agent().deploy(
        gcloud=gcloud,
        assignment="Deploy gcr.io/google-samples/hello-app:1.0 as a public service",
        project_id="my-project",
        service_name="my-service",
        region="us-central1",
    )
    print(result)
```

## Authentication

This module requires an authenticated `gcloud` container (via `gcp-auth` module).

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
# Set environment variables
export ANTHROPIC_API_KEY="your-api-key"

# Optionally specify a different model (defaults to claude-sonnet-4-5)
export ANTHROPIC_MODEL="claude-opus-4-5-20251101"

# Run the agent
dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

#### Using OpenAI (GPT)

```shell
# Set environment variables
export OPENAI_API_KEY="your-api-key"

# Optionally specify a different model (defaults to gpt-4o)
export OPENAI_MODEL="gpt-4-turbo"

# Run the agent
dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

#### Using Google Gemini

```shell
# Set environment variables
export GEMINI_API_KEY="your-api-key"

# Optionally specify a different model (defaults to gemini-2.0-flash)
export GEMINI_MODEL="gemini-1.5-pro"

# Run the agent
dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

#### Using Local Models (Docker Model Runner / Ollama)

```shell
# Configure for local model
export OPENAI_BASE_URL="http://model-runner.docker.internal/engines/v1/"
export OPENAI_MODEL="index.docker.io/ai/qwen2.5:7B-F16"
export OPENAI_DISABLE_STREAMING="true"

# Run the agent
dagger call deploy \
  --gcloud=<authenticated-container> \
  --assignment="Deploy my-image as a public service" \
  --project-id=my-project \
  --service-name=my-service
```

Dagger will automatically detect which provider to use based on the environment variables set. You can also use a `.env` file in the current directory.

## Dependencies

- [gcp-cloud-run](../gcp-cloud-run) - Cloud Run service/job operations
- [gcp-artifact-registry](../gcp-artifact-registry) - Container image publishing
