"""GCP Cloud Run Agent - AI-powered deployment and troubleshooting."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpCloudRunAgent:
    """AI-powered Cloud Run deployment and troubleshooting agent."""

    @function
    async def deploy(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        assignment: Annotated[str, Doc("Deployment instructions (e.g. 'Deploy image X as service Y, allow unauthenticated')")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_name: Annotated[str, Doc("Target Cloud Run service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        source: Annotated[dagger.Directory | None, Doc("Source directory to build (optional, if not using a pre-built image)")] = None,
        repository: Annotated[str, Doc("Artifact Registry repository for built images")] = "",
    ) -> str:
        """Deploy a service to Cloud Run using an AI agent.

        The agent interprets the assignment, builds containers if needed,
        deploys to Cloud Run, and verifies the deployment.
        """
        tools = dag.cloud_run_tools(
            gcloud=gcloud,
            project_id=project_id,
            region=region,
        )

        env = (
            dag.env()
            .with_string_input("assignment", assignment, "The deployment task to accomplish")
            .with_string_input("service_name", service_name, "The target Cloud Run service name")
            .with_string_input("project_id", project_id, "The GCP project ID")
            .with_string_input("region", region, "The GCP region to deploy to")
            .with_cloud_run_tools_input("cloud_run", tools, "Cloud Run and Artifact Registry tools")
        )

        if source:
            env = env.with_directory_input("source", source, "Source code directory to build")
        if repository:
            env = env.with_string_input("repository", repository, "Artifact Registry repository name")

        env = env.with_string_output("result", "The deployment result including the service URL or error details")

        prompt_file = dag.current_module().source().file("src/gcp_cloud_run_agent/deploy_prompt.md")

        work = dag.llm().with_env(env).with_prompt_file(prompt_file)
        return await work.env().output("result").as_string()

    @function
    async def troubleshoot(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        service_name: Annotated[str, Doc("Cloud Run service name to troubleshoot")],
        issue: Annotated[str, Doc("Description of the issue to diagnose")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Troubleshoot a Cloud Run service using an AI agent.

        The agent checks the service status, reads logs, and provides
        a diagnosis with recommended actions.
        """
        tools = dag.cloud_run_tools(
            gcloud=gcloud,
            project_id=project_id,
            region=region,
        )

        prompt = f"""You are a Cloud Run troubleshooting expert. Diagnose the following issue
with the service "{service_name}" in project "{project_id}" (region: {region}).

Issue reported: {issue}

Steps:
1. Check if the service exists using service_exists
2. If it exists, get its URL using get_service_url
3. Read the service logs using get_service_logs (check for errors with log_filter="severity>=ERROR")
4. Also read recent general logs using get_service_logs with default filter
5. Based on the logs and service state, provide a diagnosis

Write your findings to the result output. Include:
- Service status (exists/not found, URL if available)
- Key log entries related to the issue
- Root cause analysis
- Recommended actions to resolve the issue
"""

        env = (
            dag.env()
            .with_string_input("service_name", service_name, "The Cloud Run service to troubleshoot")
            .with_string_input("issue", issue, "The issue description to diagnose")
            .with_cloud_run_tools_input("cloud_run", tools, "Cloud Run tools for diagnosis")
            .with_string_output("result", "Diagnosis and recommended actions")
        )

        work = dag.llm().with_env(env).with_prompt(prompt)
        return await work.env().output("result").as_string()
