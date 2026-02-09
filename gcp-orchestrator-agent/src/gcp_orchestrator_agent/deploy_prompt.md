# Deployment Task

Deploy a service to Google Cloud Platform based on the assignment provided.

## Inputs Available

- **assignment**: The deployment task describing what to deploy and how
- **service_name** (may not be present): The target service name. If not provided, determine it from the DAGGER.md repository context or the assignment text. If you cannot determine it, report what's missing.
- **project_id**: The GCP project ID
- **region**: The GCP region to deploy to
- **source** (optional): Source code directory to build into a container
- **repository** (optional): Artifact Registry repository for storing built images

## Tools Available

### Cloud Run (via tools)

- `deploy_service`: Deploy a container image to Cloud Run
- `delete_service`: Delete a Cloud Run service
- `get_service_url`: Get the URL of a deployed service
- `service_exists`: Check if a service already exists
- `get_service_logs`: Read logs from a service

### Artifact Registry (via tools)

- `publish_container`: Publish a container to Artifact Registry
- `list_images`: List images in Artifact Registry

### Firebase Hosting (via tools)

- `deploy_firebase_hosting`: Deploy a web app to Firebase Hosting
- `deploy_firebase_preview`: Deploy to a Firebase preview channel
- `delete_firebase_channel`: Delete a Firebase preview channel

### Vertex AI (via tools)

- `deploy_vertex_model`: Deploy a containerized ML model to Vertex AI
- `list_vertex_models`: List Vertex AI models
- `list_vertex_endpoints`: List Vertex AI endpoints

### Health Check (via tools)

- `check_http_health`: Run an HTTP health check on a container
- `check_tcp_health`: Run a TCP health check on a container

### GCP Documentation (via tools, optional)

- `search_gcp_docs`: Search Google's official developer documentation for any GCP topic
- `get_gcp_doc`: Retrieve the full content of a documentation page (use parent from search results)
- `batch_get_gcp_docs`: Retrieve multiple documentation pages at once

### Diagnostic tools (via gcp_orchestrator_agent)

- `describe_service`: Get the full Cloud Run service configuration as JSON
- `list_services`: List all Cloud Run services in the project
- `get_revisions`: Get the revision history for a Cloud Run service
- `check_iam_policy`: Check IAM policy bindings on a Cloud Run service
- `list_vertex_models`: List Vertex AI models
- `list_vertex_endpoints`: List Vertex AI endpoints

## Deployment Patterns

### Cloud Run Deployment

1. Use `service_exists` to check if the service is already deployed
2. If `source` is provided, build and publish using `publish_container`
3. Deploy with `deploy_service` using the assignment's configuration
4. Verify with `get_service_url` and `get_service_logs`

### Firebase Hosting Deployment

1. Use `deploy_firebase_hosting` with the source directory
2. For preview deployments, use `deploy_firebase_preview` with a channel ID

### Vertex AI Deployment

1. Use `list_vertex_models` to check existing models
2. Deploy with `deploy_vertex_model` using the model image and configuration
3. Verify with `list_vertex_endpoints`

## Output

Write the deployment result to the `result` output. Include:
- Whether this was a new deployment or an update
- The service URL or endpoint
- Any relevant configuration applied
- Errors encountered (if any)

## Important Notes

- Always use the provided `service_name` if available — do not invent service names
- If the assignment mentions "allow unauthenticated" or "public access", set `allow_unauthenticated=True`
- Default to scale-to-zero (`min_instances=0`) unless specified otherwise
- If deployment fails, include the error details in the result
- **Priority order for all settings**: explicit inputs > DAGGER.md context > gcloud config > defaults. For example, if the assignment says port 3000 but DAGGER.md says port 8080, use port 3000 (assignment is explicit).
