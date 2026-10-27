# GCP Cloud Run - Dagger Module

Google Cloud Run deployment utilities for services and jobs.

## Installation

```bash
# Install into your workspace (dagger.toml)
dagger module install github.com/telchak/daggerverse/gcp-cloud-run@<version>

# Or add it as a dependency of your own module, from the module's directory
dagger module client add github.com/telchak/daggerverse/gcp-cloud-run@<version> --sdk=python
```

## Functions

Functions are grouped under `service` and `job`:

| Function | Description |
|----------|-------------|
| `service deploy` | Deploy a Cloud Run service |
| `service get-url` | Get URL of a deployed service |
| `service exists` | Check if a service exists |
| `service get-logs` | Read a service's logs |
| `service delete` | Delete a service |
| `job deploy` | Deploy a Cloud Run job |
| `job execute` | Execute a Cloud Run job |
| `job get-logs` | Read a job's logs |
| `job delete` | Delete a job |

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

# Deploy a service
await dag.gcp_cloud_run().service().deploy(
    gcloud=gcloud,
    image="gcr.io/my-project/my-service:latest",
    service_name="my-service",
    min_instances=0,
    max_instances=10,
    allow_unauthenticated=True,
)

# Get service URL
url = await dag.gcp_cloud_run().service().get_url(
    gcloud=gcloud,
    service_name="my-service",
)

# Deploy and execute a job
await dag.gcp_cloud_run().job().deploy(
    gcloud=gcloud,
    image="gcr.io/my-project/my-job:latest",
    job_name="my-job",
    tasks=5,
    parallelism=3,
)

await dag.gcp_cloud_run().job().execute(
    gcloud=gcloud,
    job_name="my-job",
    wait=True,
)
```

### CLI

```bash
# Deploy a service (gcloud container passed from gcp-auth)
dagger api call gcp-cloud-run service deploy \
  --gcloud=FROM_GCP_AUTH \
  --image=gcr.io/my-project/my-service:latest \
  --service-name=my-service \
  --min-instances=0 \
  --max-instances=10

# Get service URL
dagger api call gcp-cloud-run service get-url \
  --gcloud=FROM_GCP_AUTH \
  --service-name=my-service
```

## Parameters

### Service Deployment

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gcloud` | Container | required | Authenticated gcloud container |
| `image` | string | required | Container image URI |
| `service_name` | string | required | Service name |
| `region` | string | `us-central1` | GCP region |
| `port` | int | `8080` | Container port |
| `cpu` | string | `1` | CPU allocation |
| `memory` | string | `512Mi` | Memory allocation |
| `min_instances` | int | `0` | Min instances (0 = scale to zero) |
| `max_instances` | int | `10` | Max instances |
| `concurrency` | int | `80` | Max concurrent requests |
| `timeout` | string | `300s` | Request timeout |
| `allow_unauthenticated` | bool | `false` | Allow public access |
| `env_vars` | list | `[]` | Environment variables (KEY=VALUE) |
| `secrets` | list | `[]` | Secret Manager secrets |
| `vpc_connector` | string | `""` | VPC connector name |
| `service_account` | string | `""` | Service account email |

### Job Deployment

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gcloud` | Container | required | Authenticated gcloud container |
| `image` | string | required | Container image URI |
| `job_name` | string | required | Job name |
| `region` | string | `us-central1` | GCP region |
| `cpu` | string | `1` | CPU allocation |
| `memory` | string | `512Mi` | Memory allocation |
| `max_retries` | int | `0` | Max retry attempts |
| `timeout` | string | `600s` | Task timeout |
| `parallelism` | int | `1` | Parallel tasks |
| `tasks` | int | `1` | Total tasks |

## License

Apache 2.0
