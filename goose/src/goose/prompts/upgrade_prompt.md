# Service Upgrade Task

Upgrade a GCP service's version, configuration, or traffic split.

## Inputs Available

- **service_name**: The service to upgrade
- **project_id**: The GCP project ID
- **region**: The GCP region
- **target_version** (optional): Target version, image tag, or config change description
- **dry_run** (optional): If "true", only analyze and report — do not apply changes

## Upgrade Steps

1. **Inspect current state**: Use `describe_service` to get the current configuration
2. **Check revisions**: Use `get_revisions` to see the deployment history
3. **Plan the upgrade**: Determine what needs to change based on target_version
4. **Apply changes**: Deploy the new version or configuration
5. **Verify**: Check the service is healthy after the upgrade

## Supported Upgrade Scenarios

### Image Version Update
- Deploy a new container image tag to an existing Cloud Run service
- Use `deploy_service` with the new image URI

### Traffic Splitting
- Gradually shift traffic between revisions
- Use gcloud commands via `describe_service` to understand current traffic

### Configuration Change
- Update environment variables, resources, scaling settings
- Redeploy with updated configuration

### Firebase Redeployment
- Rebuild and redeploy a Firebase Hosting site
- Use `deploy_firebase_hosting` with updated source

## Output

Write the upgrade result to the `result` output. Include:
- Previous state (version, configuration)
- Changes applied (or planned if dry_run)
- New state after upgrade
- Verification results
- Any rollback instructions if needed
