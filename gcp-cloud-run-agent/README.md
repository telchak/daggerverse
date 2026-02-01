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

This module requires:
- An authenticated `gcloud` container (via `gcp-auth` module)
- The `ANTHROPIC_API_KEY` environment variable set for the Dagger engine (LLM provider)

## Dependencies

- [gcp-cloud-run](../gcp-cloud-run) - Cloud Run service/job operations
- [gcp-artifact-registry](../gcp-artifact-registry) - Container image publishing
