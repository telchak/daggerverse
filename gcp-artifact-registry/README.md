# GCP Artifact Registry - Dagger Module

Google Cloud Artifact Registry operations for publishing and managing container images.

## Installation

```bash
dagger install github.com/telchak/daggerverse/gcp-artifact-registry
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

This module accepts a pre-authenticated `gcloud` container. Use `gcp-auth` to get one:

### CLI

```bash
# Get gcloud container from gcp-auth, then use it
dagger call -m gcp-auth gcloud-container \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project

# Publish with authenticated gcloud container
dagger call publish \
  --container=FROM_BUILD \
  --project-id=my-project \
  --repository=my-repo \
  --image-name=my-image \
  --tag=v1.0.0 \
  --gcloud=FROM_GCP_AUTH
```

### Python Example

```python
from dagger import dag

# Get authenticated gcloud container from gcp-auth
gcloud = dag.gcp_auth().gcloud_container(
    credentials=credentials,
    project_id="my-project",
)

# Publish container
image_ref = await dag.gcp_artifact_registry().publish(
    container=my_container,
    project_id="my-project",
    repository="my-repo",
    image_name="my-image",
    tag="v1.0.0",
    gcloud=gcloud,
)

# List images
images = await dag.gcp_artifact_registry().list_images(
    gcloud=gcloud,
    project_id="my-project",
    repository="my-repo",
)
```

### Local Development

If you've already configured Docker with `gcloud auth configure-docker`, you can pass your local Docker config directly instead of providing a `gcloud` container:

```bash
dagger call publish \
  --container=FROM_BUILD \
  --project-id=my-project \
  --repository=my-repo \
  --image-name=my-image \
  --tag=v1.0.0 \
  --docker-config=$HOME/.docker/config.json
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gcloud` | Container | Yes* | Authenticated gcloud container |
| `docker_config` | File | No | Docker config.json with registry credentials |
| `container` | Container | Yes | Container to publish |
| `project_id` | string | Yes | GCP project ID |
| `repository` | string | Yes | Repository name |
| `image_name` | string | Yes | Image name |
| `region` | string | No | GCP region (default: us-central1) |
| `tag` | string | No | Image tag (default: latest) |

*`gcloud` is optional for `publish` if you provide `docker_config` or just want to push without auth. Required for other functions.

## License

Apache 2.0
