"""GCP Orchestrator Agent - AI-powered multi-service GCP deployment and troubleshooting."""

from typing import Annotated

import dagger
from dagger import Doc, dag, field, function, object_type


@object_type
class GcpOrchestratorAgent:
    """AI-powered GCP deployment and troubleshooting agent.

    Supports Cloud Run, Firebase Hosting, Vertex AI, and health checks.
    """

    gcloud: Annotated[dagger.Container | None, Doc("Authenticated gcloud container")] = field(default=None)
    project_id: Annotated[str, Doc("GCP project ID")] = field(default="")
    region: Annotated[str, Doc("GCP region")] = field(default="us-central1")
    credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (required for Firebase)")] = field(
        default=None
    )
    developer_knowledge_api_key: Annotated[
        dagger.Secret | None,
        Doc("Google Developer Knowledge API key (optional, enables searching GCP documentation)"),
    ] = field(default=None)

    def _load_prompt(self, filename: str) -> dagger.File:
        """Load a prompt file from the module source."""
        return dag.current_module().source().file(f"src/gcp_orchestrator_agent/{filename}")

    async def _read_dagger_md(self, source: dagger.Directory | None) -> str:
        """Read DAGGER.md from a source directory for per-repo context."""
        if not source:
            return ""
        entries = await source.entries()
        if "DAGGER.md" not in entries:
            return ""
        contents = await source.file("DAGGER.md").contents()
        return f"\n\n## Repository Context (from DAGGER.md)\n\n{contents}"

    async def _build_llm(
        self,
        env: dagger.Env,
        prompt_file: str,
        source: dagger.Directory | None = None,
    ) -> dagger.LLM:
        """Build an LLM with the environment, current module tools, and prompts."""
        dagger_md = await self._read_dagger_md(source)

        system_prompt = await self._load_prompt("system_prompt.md").contents()

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(system_prompt + dagger_md)
        )

        return (
            llm
            .with_blocked_function("GcpOrchestratorAgent", "deploy")
            .with_blocked_function("GcpOrchestratorAgent", "troubleshoot")
            .with_prompt_file(self._load_prompt(prompt_file))
        )

    # --- Agent entrypoints (called by the user) ---

    @function
    async def deploy(
        self,
        assignment: Annotated[str, Doc("Deployment instructions (e.g. 'Deploy image X as service Y, allow unauthenticated')")],
        service_name: Annotated[str, Doc("Target service name")],
        source: Annotated[dagger.Directory | None, Doc("Source directory to build (optional, if not using a pre-built image)")] = None,
        repository: Annotated[str, Doc("Artifact Registry repository for built images")] = "",
    ) -> str:
        """Deploy a service using an AI agent.

        Supports Cloud Run, Firebase Hosting, and Vertex AI deployments.
        The agent interprets the assignment and uses the appropriate tools.
        If the source directory contains a DAGGER.md file, it will be used
        as additional context for the agent.
        """
        tools = dag.orchestrator_tools(
            gcloud=self.gcloud,
            project_id=self.project_id,
            region=self.region,
            credentials=self.credentials,
            developer_knowledge_api_key=self.developer_knowledge_api_key,
        )

        env = (
            dag.env()
            .with_string_input("assignment", assignment, "The deployment task to accomplish")
            .with_string_input("service_name", service_name, "The target service name")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region to deploy to")
            .with_orchestrator_tools_input("tools", tools, "GCP deployment and operations tools")
        )

        if source:
            env = env.with_directory_input("source", source, "Source code directory to build")
        if repository:
            env = env.with_string_input("repository", repository, "Artifact Registry repository name")

        env = env.with_string_output("result", "The deployment result including the service URL or error details")

        work = await self._build_llm(env, "deploy_prompt.md", source)
        return await work.env().output("result").as_string()

    @function
    async def troubleshoot(
        self,
        service_name: Annotated[str, Doc("Service name to troubleshoot")],
        issue: Annotated[str, Doc("Description of the issue to diagnose")],
        source: Annotated[dagger.Directory | None, Doc("Source directory (optional, for DAGGER.md context)")] = None,
    ) -> str:
        """Troubleshoot a GCP service using an AI agent.

        The agent checks the service status, reads logs, and provides
        a diagnosis with recommended actions. Supports Cloud Run,
        Firebase, and Vertex AI services.
        If the source directory contains a DAGGER.md file, it will be used
        as additional context for the agent.
        """
        tools = dag.orchestrator_tools(
            gcloud=self.gcloud,
            project_id=self.project_id,
            region=self.region,
            credentials=self.credentials,
            developer_knowledge_api_key=self.developer_knowledge_api_key,
        )

        env = (
            dag.env()
            .with_string_input("service_name", service_name, "The service to troubleshoot")
            .with_string_input("issue", issue, "The issue description to diagnose")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region")
            .with_orchestrator_tools_input("tools", tools, "GCP tools for diagnosis")
            .with_string_output("result", "Diagnosis and recommended actions")
        )

        work = await self._build_llm(env, "troubleshoot_prompt.md", source)
        return await work.env().output("result").as_string()

    # --- Utility functions (exposed to the LLM via with_current_module) ---

    @function
    async def describe_service(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name")],
    ) -> str:
        """Get the full configuration of a Cloud Run service as JSON."""
        return await (
            self.gcloud
            .with_exec([
                "gcloud", "run", "services", "describe", service_name,
                "--region", self.region,
                "--project", self.project_id,
                "--format", "json",
            ])
            .stdout()
        )

    @function
    async def list_services(self) -> str:
        """List all Cloud Run services in the project and region."""
        return await (
            self.gcloud
            .with_exec([
                "gcloud", "run", "services", "list",
                "--region", self.region,
                "--project", self.project_id,
                "--format", "json",
            ])
            .stdout()
        )

    @function
    async def get_revisions(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name")],
    ) -> str:
        """Get the revision history for a Cloud Run service."""
        return await (
            self.gcloud
            .with_exec([
                "gcloud", "run", "revisions", "list",
                "--service", service_name,
                "--region", self.region,
                "--project", self.project_id,
                "--format", "json",
            ])
            .stdout()
        )

    @function
    async def check_iam_policy(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name")],
    ) -> str:
        """Check the IAM policy bindings on a Cloud Run service."""
        return await (
            self.gcloud
            .with_exec([
                "gcloud", "run", "services", "get-iam-policy", service_name,
                "--region", self.region,
                "--project", self.project_id,
                "--format", "json",
            ])
            .stdout()
        )

    @function
    async def list_vertex_models(self) -> str:
        """List all Vertex AI models in the project."""
        return await (
            self.gcloud
            .with_exec([
                "gcloud", "ai", "models", "list",
                f"--region={self.region}",
            ])
            .stdout()
        )

    @function
    async def list_vertex_endpoints(self) -> str:
        """List all Vertex AI endpoints in the project."""
        return await (
            self.gcloud
            .with_exec([
                "gcloud", "ai", "endpoints", "list",
                f"--region={self.region}",
            ])
            .stdout()
        )
