# Troubleshooting Task

Diagnose and troubleshoot the reported issue with a GCP service.

## Inputs Available

- **service_name** (may not be present): The service to troubleshoot. If not provided, determine it from the project context or the issue description. If you cannot determine it, report what's missing.
- **issue**: The reported issue description to diagnose
- **project_id**: The GCP project ID
- **region**: The GCP region

## Troubleshooting Steps

### Cloud Run Services

1. **Check service state**: Use `service_exists` to verify the service is deployed
2. **Get service URL**: If the service exists, use `get_service_url` to retrieve its endpoint
3. **Inspect configuration**: Use `describe_service` to get the full config — check for misconfigurations
4. **Check error logs**: Use `get_service_logs` with `log_filter="severity>=ERROR"` to find error entries. For richer log queries (advanced filters, wider time ranges, cross-service correlation), use the `gcloud` MCP server's Cloud Logging tools.
5. **Check recent logs**: Use `get_service_logs` with default filter to get general activity
6. **Check metrics**: Use the `gcloud` MCP server to query Cloud Monitoring metrics (request latency, error rates, CPU/memory utilization) for anomalies
7. **Check traces**: If the issue involves latency or timeout problems, use the `gcloud` MCP server's Cloud Trace tools to analyze distributed traces
8. **Check revisions**: Use `get_revisions` if the issue started after a recent deployment
9. **Check IAM**: Use `check_iam_policy` if the issue involves authentication or permission errors
10. **Search docs**: If the error is unfamiliar, use `search_gcp_docs` to find relevant documentation (if available)
11. **Analyze**: Correlate all findings with the reported issue

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
- **Priority order**: explicit inputs > project context > gcloud config > defaults
