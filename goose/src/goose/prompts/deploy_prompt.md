# Deployment Task

**YOUR #1 JOB: Call `deploy_service` (or another deployment tool) to deploy the service.** If you finish without calling a deployment tool, the task has FAILED. Do not just analyze or describe — execute the deployment, then set the `result` output.

## Steps

1. Call `deploy_service` with the image, service name, project, and region from the inputs
2. Set the `result` output with the deployment URL and details

Do NOT skip step 1. Do NOT end your turn without having called a deployment tool.

## Inputs Available

- **assignment**: The deployment task describing what to deploy and how
- **service_name** (may not be present): The target service name. If not provided, determine it from the project context or the assignment text.
- **project_id**: The GCP project ID
- **region**: The GCP region to deploy to
- **source** (optional): Source code directory to build into a container
- **repository** (optional): Artifact Registry repository for storing built images

## Deployment Patterns

- **Cloud Run**: Call `deploy_service` with the image and configuration
- **Firebase Hosting**: Call `deploy_firebase_hosting` with the source directory
- **Vertex AI**: Call `deploy_vertex_model` with the model image

## Important Notes

- If the assignment mentions "allow unauthenticated" or "public access", set `allow_unauthenticated=True`
- Default to scale-to-zero (`min_instances=0`) unless specified otherwise
- If deployment fails, include the error details in the result

## Reminder

You MUST call a deployment tool AND set the `result` output. This is not optional.
