# GCP Artifact Registry - Dagger Module

Google Cloud Artifact Registry operations for publishing and managing container images.

## Installation

```bash
dagger install github.com/YOUR_ORG/daggerverse/gcp-artifact-registry
```

## Functions

| Function | Description |
|----------|-------------|
| `publish` | Publish container to Artifact Registry |
| `create-repository` | Create a new repository |
| `list-images` | List images in a repository |
| `get-image-uri` | Construct full image URI |
| `upload-generic` | Upload files to a generic repository |

## Usage

### Publish Container

```bash
dagger call publish \
  --container=FROM_BUILD \
  --project-id=my-project \
  --repository=my-repo \
  --image-name=my-image \
  --tag=v1.0.0 \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS
```

### Python Example

```python
from dagger import dag

image_ref = await dag.gcp_artifact_registry().publish(
    container=my_container,
    project_id="my-project",
    repository="my-repo",
    image_name="my-image",
    tag="v1.0.0",
    credentials=credentials,
)
```

## Dependencies

- `gcp-auth` - For GCP authentication

## License

Apache 2.0
