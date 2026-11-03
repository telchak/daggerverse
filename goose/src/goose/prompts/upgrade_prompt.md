# Service Upgrade Task

Upgrade a GCP service's version, configuration, or traffic split.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **service_name**: The service to upgrade
- **project_id**: The GCP project ID
- **region**: The GCP region
- **target_version** (optional): Target version, image tag, or config change description
- **dry_run** (optional): If "true", only analyze and report — do NOT apply any changes

## Upgrade Steps

1. **Inspect current state**: Use `describeService` to get the current configuration
2. **Check revisions**: Use `getRevisions` to see the deployment history
3. **Plan the upgrade**: Determine what needs to change based on target_version

**If dry_run is "true"**: Stop here. Give the analysis in your final reply and do NOT proceed to steps 4-5. Do not query logs, metrics, or traces — the goal is a quick comparison of current vs target state.

4. **Apply changes**: Deploy the new version or configuration
5. **Verify**: Check the service is healthy after the upgrade

## Be efficient

- Use the built-in tools (`describeService`, `getRevisions`, `deployService`) for the upgrade workflow.
- For a dry run, you should need at most 2-3 tool calls (describe + revisions), then write your analysis.

## Supported Upgrade Scenarios

### Image Version Update
- Deploy a new container image tag to an existing Cloud Run service
- Use `deployService` with the new image URI

### Traffic Splitting
- Gradually shift traffic between revisions
- Use gcloud commands via `describeService` to understand current traffic

### Configuration Change
- Update environment variables, resources, scaling settings
- Redeploy with updated configuration

### Firebase Redeployment
- Rebuild and redeploy a Firebase Hosting site
- Use `deployFirebaseHosting` with updated source

## Output

**CRITICAL**: Your final reply is the findings: write all of it there.

Include:
- Previous state (version, configuration)
- Changes applied (or planned if dry_run)
- New state after upgrade (skip if dry_run)
- Verification results (skip if dry_run)
- Any rollback instructions if needed
