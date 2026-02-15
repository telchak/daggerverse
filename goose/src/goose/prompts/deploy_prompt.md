# Deployment Task

Deploy a service to Google Cloud Platform based on the assignment provided.

## Inputs Available

- **assignment**: The deployment task describing what to deploy and how
- **service_name** (may not be present): The target service name. If not provided, determine it from the project context or the assignment text. If you cannot determine it, report what's missing.
- **project_id**: The GCP project ID
- **region**: The GCP region to deploy to
- **source** (optional): Source code directory to build into a container
- **repository** (optional): Artifact Registry repository for storing built images

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

- If the assignment mentions "allow unauthenticated" or "public access", set `allow_unauthenticated=True`
- Default to scale-to-zero (`min_instances=0`) unless specified otherwise
- If deployment fails, include the error details in the result
