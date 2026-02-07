# Troubleshooting Task

Diagnose and troubleshoot the reported issue with a GCP service.

## Inputs Available

- **service_name**: The service to troubleshoot
- **issue**: The reported issue description to diagnose
- **project_id**: The GCP project ID
- **region**: The GCP region

## Tools Available

### Cloud Run (via tools)

- `service_exists`: Check if the service exists
- `get_service_url`: Get the URL of the service
- `get_service_logs`: Read logs from the service (supports `log_filter` parameter)

### GCP Documentation (via tools, optional)

- `search_gcp_docs`: Search official GCP documentation for error messages, configuration options, or known issues
- `get_gcp_doc`: Retrieve full documentation page content
- `batch_get_gcp_docs`: Retrieve multiple documentation pages

### Diagnostic tools (via gcp_orchestrator_agent)

- `describe_service`: Get the full Cloud Run service configuration as JSON
- `list_services`: List all Cloud Run services in the project
- `get_revisions`: Get the revision history for a service
- `check_iam_policy`: Check IAM policy bindings on a service
- `list_vertex_models`: List Vertex AI models (for ML service issues)
- `list_vertex_endpoints`: List Vertex AI endpoints (for ML service issues)

## Troubleshooting Steps

### Cloud Run Services

1. **Check service state**: Use `service_exists` to verify the service is deployed
2. **Get service URL**: If the service exists, use `get_service_url` to retrieve its endpoint
3. **Inspect configuration**: Use `describe_service` to get the full config — check for misconfigurations
4. **Check error logs**: Use `get_service_logs` with `log_filter="severity>=ERROR"` to find error entries
5. **Check recent logs**: Use `get_service_logs` with default filter to get general activity
6. **Check revisions**: Use `get_revisions` if the issue started after a recent deployment
7. **Check IAM**: Use `check_iam_policy` if the issue involves authentication or permission errors
8. **Search docs**: If the error is unfamiliar, use `search_gcp_docs` to find relevant documentation (if available)
9. **Analyze**: Correlate all findings with the reported issue

### Common Cloud Run Issues

- **502/503 errors**: Check container startup, port configuration, health checks, memory limits
- **Permission denied**: Check IAM policies, service account permissions, allow-unauthenticated setting
- **Slow startup**: Check min-instances, container image size, initialization code
- **Connection reset**: Check port binding, timeout settings, max instances

### Vertex AI Services

1. Use `list_vertex_models` and `list_vertex_endpoints` to check model/endpoint state
2. Verify the model is deployed to an active endpoint

### Firebase Hosting

1. For Firebase issues, check the deployment status and any build errors reported

## Output

Write your diagnosis to the `result` output. Include:
- Service status (exists/not found, URL if available)
- Key log entries related to the issue
- Root cause analysis
- Recommended actions to resolve the issue
- If a DAGGER.md context is present, reference any project-specific configuration that may be relevant
