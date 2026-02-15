# Troubleshooting Task

Diagnose and troubleshoot the reported issue with a GCP service.

## Inputs Available

- **service_name** (may not be present): The service to troubleshoot. If not provided, determine it from the project context or the issue description. If you cannot determine it, report what's missing.
- **issue**: The reported issue description to diagnose
- **project_id**: The GCP project ID
- **region**: The GCP region

## Troubleshooting Steps

### Cloud Run Services

1. **Verify and inspect**: Use `service_exists` to confirm the service is deployed, then `describe_service` to get the full configuration
2. **Read logs**: Use `get_service_logs` with `log_filter="severity>=ERROR"` to find error entries
3. **Investigate based on findings** — use additional tools as the evidence suggests:
   - Permission errors → `check_iam_policy`
   - Recent deployment regression → `get_revisions`
   - Latency/timeout issues → Cloud Trace via gcloud MCP
   - Unfamiliar errors → `search_gcp_docs` (if available)
   - Need richer log queries or metrics → gcloud MCP
4. **Diagnose**: Correlate all findings with the reported issue

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
