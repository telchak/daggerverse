# GCP Cloud Run Dagger Module

Simple, reusable Dagger module for deploying services and jobs to Google Cloud Run.

## Features

- Deploy Cloud Run services with full configuration
- Deploy and execute Cloud Run jobs
- Manage traffic splitting between revisions
- Configure IAM policies
- Scale to zero for cost optimization
- VPC connector and secrets support

## Usage

### Deploy a Service

```python
import dagger

async with dagger.Connection() as client:
    result = await (
        client.gcp_cloud_run()
        .deploy_service(
            image="gcr.io/my-project/my-service:latest",
            service_name="my-service",
            credentials=client.set_secret("gcp_creds", gcp_json),
            project_id="my-project",
            region="us-central1",
            min_instances=0,  # Scale to zero
            max_instances=10,
            env_vars=["ENV=production", "DEBUG=false"],
        )
    )
```

### Deploy a Job

```python
result = await (
    client.gcp_cloud_run()
    .deploy_job(
        image="gcr.io/my-project/my-job:latest",
        job_name="my-job",
        credentials=credentials,
        project_id="my-project",
        region="us-central1",
        tasks=5,
        parallelism=3,
    )
)
```

### Execute a Job

```python
result = await (
    client.gcp_cloud_run()
    .execute_job(
        job_name="my-job",
        credentials=credentials,
        project_id="my-project",
        region="us-central1",
        wait=True,
    )
)
```

### Get Service URL

```python
url = await (
    client.gcp_cloud_run()
    .get_service_url(
        service_name="my-service",
        credentials=credentials,
        project_id="my-project",
        region="us-central1",
    )
)
```

### Traffic Splitting

```python
result = await (
    client.gcp_cloud_run()
    .update_traffic(
        service_name="my-service",
        revisions=["my-service-00001-xyz=80", "my-service-00002-abc=20"],
        credentials=credentials,
        project_id="my-project",
        region="us-central1",
    )
)
```

### Make Service Public

```python
result = await (
    client.gcp_cloud_run()
    .set_iam_policy(
        service_name="my-service",
        member="allUsers",
        role="roles/run.invoker",
        credentials=credentials,
        project_id="my-project",
        region="us-central1",
    )
)
```

## CLI Usage

```bash
# Deploy a service
dagger call deploy-service \
  --image=gcr.io/my-project/my-service:latest \
  --service-name=my-service \
  --credentials=env:GCP_CREDENTIALS \
  --project-id=my-project \
  --region=us-central1 \
  --min-instances=0 \
  --max-instances=10

# Deploy a job
dagger call deploy-job \
  --image=gcr.io/my-project/my-job:latest \
  --job-name=my-job \
  --credentials=env:GCP_CREDENTIALS \
  --project-id=my-project \
  --tasks=5

# Execute a job
dagger call execute-job \
  --job-name=my-job \
  --credentials=env:GCP_CREDENTIALS \
  --project-id=my-project \
  --wait=true

# Get service URL
dagger call get-service-url \
  --service-name=my-service \
  --credentials=env:GCP_CREDENTIALS \
  --project-id=my-project
```

## Parameters

### Service Deployment

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | string | required | Container image URI |
| `service_name` | string | required | Service name |
| `credentials` | Secret | required | GCP credentials |
| `project_id` | string | required | GCP project ID |
| `region` | string | `us-central1` | GCP region |
| `port` | int | `8080` | Container port |
| `cpu` | string | `1` | CPU allocation |
| `memory` | string | `512Mi` | Memory allocation |
| `min_instances` | int | `0` | Min instances (0 = scale to zero) |
| `max_instances` | int | `10` | Max instances |
| `concurrency` | int | `80` | Max concurrent requests |
| `timeout` | string | `300s` | Request timeout |
| `allow_unauthenticated` | bool | `false` | Allow public access |
| `env_vars` | list[str] | `[]` | Environment variables (KEY=VALUE) |
| `secrets` | list[str] | `[]` | Secret Manager secrets (NAME=VERSION) |
| `vpc_connector` | string | `""` | VPC connector name |
| `service_account` | string | `""` | Service account email |

### Job Deployment

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | string | required | Container image URI |
| `job_name` | string | required | Job name |
| `credentials` | Secret | required | GCP credentials |
| `project_id` | string | required | GCP project ID |
| `region` | string | `us-central1` | GCP region |
| `cpu` | string | `1` | CPU allocation |
| `memory` | string | `512Mi` | Memory allocation |
| `max_retries` | int | `0` | Max retry attempts |
| `timeout` | string | `600s` | Task timeout |
| `parallelism` | int | `1` | Parallel tasks |
| `tasks` | int | `1` | Total tasks |
| `env_vars` | list[str] | `[]` | Environment variables (KEY=VALUE) |
| `secrets` | list[str] | `[]` | Secret Manager secrets (NAME=VERSION) |
| `vpc_connector` | string | `""` | VPC connector name |
| `service_account` | string | `""` | Service account email |
| `command` | list | `None` | Override command |
| `args` | list | `None` | Override args |

## Cost Optimization

Set `min_instances=0` to enable scale-to-zero and avoid continuous costs when the service is idle.

## Requirements

- Depends on the `gcp-auth` module for authentication
- GCP service account with Cloud Run Admin permissions

## License

Apache 2.0
