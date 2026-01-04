# GCP Vertex AI - Dagger Module

Google Cloud Vertex AI operations for deploying and managing ML models.

## Installation

```bash
dagger install github.com/telchak/daggerverse/gcp-vertex-ai
```

## Functions

| Function | Description |
|----------|-------------|
| `deploy-model` | Deploy a containerized model to Vertex AI |
| `list-models` | List all models |
| `list-endpoints` | List all endpoints |

## Usage

This module accepts a pre-authenticated `gcloud` container. Use `gcp-auth` to get one:

### Python Example

```python
from dagger import dag

# Get authenticated gcloud container from gcp-auth
gcloud = dag.gcp_auth().gcloud_container(
    credentials=credentials,
    project_id="my-project",
    region="us-central1",
)

# Deploy a model
result = await dag.gcp_vertex_ai().deploy_model(
    gcloud=gcloud,
    image_uri="us-central1-docker.pkg.dev/project/repo/image:tag",
    model_name="my-model",
    endpoint_name="my-endpoint",
    machine_type="n1-standard-4",
    accelerator_type="NVIDIA_TESLA_T4",
    accelerator_count=1,
)

# List models and endpoints
models = await dag.gcp_vertex_ai().list_models(gcloud=gcloud)
endpoints = await dag.gcp_vertex_ai().list_endpoints(gcloud=gcloud)
```

### CLI

```bash
# Deploy model (gcloud container passed from gcp-auth)
dagger call deploy-model \
  --gcloud=FROM_GCP_AUTH \
  --image-uri=us-central1-docker.pkg.dev/project/repo/image:tag \
  --model-name=my-model \
  --endpoint-name=my-endpoint

# List models
dagger call list-models --gcloud=FROM_GCP_AUTH
```

## License

Apache 2.0
