# GCP Vertex AI - Dagger Module

Google Cloud Vertex AI operations for deploying and managing ML models.

## Installation

```bash
dagger install github.com/YOUR_ORG/daggerverse/gcp-vertex-ai
```

## Functions

| Function | Description |
|----------|-------------|
| `deploy-model` | Deploy a containerized model to Vertex AI |
| `list-models` | List all models |
| `list-endpoints` | List all endpoints |

## Usage

### Deploy Model

```bash
dagger call deploy-model \
  --image-uri=us-central1-docker.pkg.dev/project/repo/image:tag \
  --project-id=my-project \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --model-name=my-model \
  --endpoint-name=my-endpoint
```

### Python Example

```python
from dagger import dag

result = await dag.gcp_vertex_ai().deploy_model(
    image_uri="us-central1-docker.pkg.dev/project/repo/image:tag",
    project_id="my-project",
    credentials=credentials,
    model_name="my-model",
    endpoint_name="my-endpoint",
    machine_type="n1-standard-4",
    accelerator_type="NVIDIA_TESLA_T4",
    accelerator_count=1,
)
```

## Dependencies

- `gcp-auth` - For GCP authentication

## License

Apache 2.0
