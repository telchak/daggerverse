# Deployment Task

**YOUR #1 JOB: Call `deployService` (or another deployment tool) to deploy the service.** If you finish without calling a deployment tool, the task has FAILED. Do not just analyze or describe — execute the deployment, then report it in your final reply.

## Steps

1. Call `deployService` with the image, service name, project, and region from the inputs
2. End with the deployment URL and details as your final reply

Do NOT skip step 1. Do NOT end your turn without having called a deployment tool.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **assignment**: The deployment task describing what to deploy and how
- **service_name** (may not be present): The target service name. If not provided, determine it from the project context or the assignment text.
- **project_id**: The GCP project ID
- **region**: The GCP region to deploy to
- **source** (optional): present when a source directory was given. It is your workspace: build and publish it with `buildAndPublish`, or deploy it with `deployFirebaseHosting` / `deployFirebasePreview`.
- **repository** (optional): Artifact Registry repository for storing built images

## Deployment Patterns

- **Cloud Run**: Call `deployService` with the image and configuration
- **Firebase Hosting**: Call `deployFirebaseHosting` (or `deployFirebasePreview`); both deploy the workspace
- **Vertex AI**: Call `deployVertexModel` with the model image

## Important Notes

- If the assignment mentions "allow unauthenticated" or "public access", set `allow_unauthenticated=True`
- Default to scale-to-zero (`min_instances=0`) unless specified otherwise
- If deployment fails, include the error details in the result

## Reminder

You MUST call a deployment tool AND report the result in your final reply. This is not optional.
