"""GCP Orchestrator Agent - AI-powered multi-service GCP deployment and troubleshooting."""

from typing import Annotated

import dagger
from dagger import Doc, dag, field, function, object_type


@object_type
class GcpOrchestratorAgent:
    """AI-powered GCP deployment and troubleshooting agent.

    Supports Cloud Run, Firebase Hosting, Vertex AI, and health checks.

    Authentication (pick one):
    - Pre-built gcloud container (--gcloud)
    - OIDC token + WIF provider (--oidc-token + --workload-identity-provider)
    - Service account JSON key (--credentials)
    - Host gcloud config for local dev (--google-cloud-dir ~/.config/gcloud)
    """

    # Option A: Pre-built gcloud (backward compat)
    gcloud: Annotated[dagger.Container | None, Doc("Authenticated gcloud container (pre-built)")] = field(default=None)

    # Option B: Raw credentials (agent builds gcloud + reuses for Firebase)
    oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token from any CI provider")] = field(default=None)
    workload_identity_provider: Annotated[
        str, Doc("GCP Workload Identity Federation provider resource name")
    ] = field(default="")
    service_account_email: Annotated[
        str, Doc("Service account email to impersonate (optional)")
    ] = field(default="")
    credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key")] = field(default=None)

    # Option C: Host gcloud config (local development)
    google_cloud_dir: Annotated[
        dagger.Directory | None,
        Doc("Host gcloud config directory for local dev (e.g. ~/.config/gcloud)"),
    ] = field(default=None)

    # Config (auto-discovered from gcloud if omitted)
    project_id: Annotated[str, Doc("GCP project ID (auto-discovered from gcloud if omitted)")] = field(default="")
    region: Annotated[str, Doc("GCP region (auto-discovered from gcloud, defaults to us-central1)")] = field(default="")

    # Optional
    developer_knowledge_api_key: Annotated[
        dagger.Secret | None,
        Doc("Google Developer Knowledge API key (optional, enables searching GCP documentation)"),
    ] = field(default=None)

    # --- DAGGER.md parsing ---

    async def _parse_dagger_md(self, source: dagger.Directory | None) -> dict[str, str]:
        """Parse known configuration values from DAGGER.md.

        Looks for key-value lines like:
          - Project ID: my-project
          - Region: us-central1
          - Service name: my-service
        """
        if not source:
            return {}
        entries = await source.entries()
        if "DAGGER.md" not in entries:
            return {}
        contents = await source.file("DAGGER.md").contents()

        config: dict[str, str] = {}
        key_map = {
            "project id": "project_id",
            "project_id": "project_id",
            "region": "region",
            "service name": "service_name",
            "service_name": "service_name",
        }
        for line in contents.splitlines():
            stripped = line.strip().lstrip("- ")
            for prefix, key in key_map.items():
                if stripped.lower().startswith(prefix + ":"):
                    value = stripped.split(":", 1)[1].strip().strip("`")
                    if value:
                        config[key] = value
                    break
        return config

    # --- Resolution methods ---
    #
    # Priority order: explicit args → DAGGER.md → gcloud config → defaults

    async def _resolve_project_id_early(self) -> str:
        """Resolve project_id without needing a gcloud container.

        Used when building gcloud from OIDC (which requires project_id).
        Checks: explicit → DAGGER.md → SA JSON → error.
        """
        if self.project_id:
            return self.project_id
        dagger_md_project = self._dagger_md_config.get("project_id", "")
        if dagger_md_project:
            return dagger_md_project
        if self.credentials:
            return await dag.gcp_auth().get_project_id(credentials=self.credentials)
        raise ValueError(
            "--project-id is required when using --oidc-token "
            "(OIDC tokens don't contain project_id)"
        )

    async def _resolve_gcloud(self) -> dagger.Container:
        """Resolve the gcloud container from available credentials."""
        if self.gcloud:
            return self.gcloud

        if self.oidc_token and self.workload_identity_provider:
            project_id = await self._resolve_project_id_early()
            kwargs: dict = {
                "oidc_token": self.oidc_token,
                "workload_identity_provider": self.workload_identity_provider,
                "project_id": project_id,
            }
            if self.service_account_email:
                kwargs["service_account_email"] = self.service_account_email
            if self.region:
                kwargs["region"] = self.region
            return dag.gcp_auth().gcloud_container_from_oidc_token(**kwargs)

        if self.credentials:
            project_id = await self._resolve_project_id_early()
            kwargs = {
                "credentials": self.credentials,
                "project_id": project_id,
            }
            if self.region:
                kwargs["region"] = self.region
            return dag.gcp_auth().gcloud_container(**kwargs)

        if self.google_cloud_dir:
            # Local dev: mount host gcloud config into a gcloud SDK container.
            # Project and region are auto-discovered from the config afterward.
            return (
                dag.container()
                .from_("google/cloud-sdk:alpine")
                .with_directory("/root/.config/gcloud", self.google_cloud_dir)
                .with_env_variable(
                    "GOOGLE_APPLICATION_CREDENTIALS",
                    "/root/.config/gcloud/application_default_credentials.json",
                )
            )

        raise ValueError(
            "No authentication provided. Supply one of:\n"
            "  --gcloud (pre-built authenticated container)\n"
            "  --oidc-token + --workload-identity-provider (CI/CD)\n"
            "  --credentials (service account JSON key)\n"
            "  --google-cloud-dir (host gcloud config for local dev, e.g. ~/.config/gcloud)"
        )

    async def _resolve_project_id(self, gcloud: dagger.Container) -> str:
        """Resolve project_id: explicit → DAGGER.md → gcloud config → error."""
        if self.project_id:
            return self.project_id
        dagger_md_project = self._dagger_md_config.get("project_id", "")
        if dagger_md_project:
            return dagger_md_project
        result = await (
            gcloud.with_exec(["gcloud", "config", "get-value", "project"])
            .stdout()
        )
        value = result.strip()
        if value and value != "(unset)":
            return value
        raise ValueError("Cannot determine project_id. Provide --project-id or set it in DAGGER.md.")

    async def _resolve_region(self, gcloud: dagger.Container) -> str:
        """Resolve region: explicit → DAGGER.md → gcloud config → default us-central1."""
        if self.region:
            return self.region
        dagger_md_region = self._dagger_md_config.get("region", "")
        if dagger_md_region:
            return dagger_md_region
        result = await (
            gcloud.with_exec(["gcloud", "config", "get-value", "compute/region"])
            .stdout()
        )
        value = result.strip()
        if value and value != "(unset)":
            return value
        return "us-central1"

    async def _resolve_all(self, source: dagger.Directory | None = None) -> dict[str, str]:
        """Resolve gcloud, project_id, and region; store back on self.

        Priority order: explicit args → DAGGER.md → gcloud config → defaults.
        Returns the parsed DAGGER.md config dict.
        """
        self._dagger_md_config = await self._parse_dagger_md(source)
        self.gcloud = await self._resolve_gcloud()
        self.project_id = await self._resolve_project_id(self.gcloud)
        self.region = await self._resolve_region(self.gcloud)
        return self._dagger_md_config

    # --- Prompt helpers ---

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
        source: Annotated[dagger.Directory | None, Doc("Source directory to build (optional, for DAGGER.md context)")] = None,
        service_name: Annotated[str, Doc("Target service name (optional, LLM reads from DAGGER.md or assignment)")] = "",
        repository: Annotated[str, Doc("Artifact Registry repository for built images")] = "",
    ) -> str:
        """Deploy a service using an AI agent.

        Supports Cloud Run, Firebase Hosting, and Vertex AI deployments.
        The agent interprets the assignment and uses the appropriate tools.
        If the source directory contains a DAGGER.md file, it will be used
        as additional context for the agent.
        """
        dagger_md_config = await self._resolve_all(source)

        # service_name priority: explicit arg → DAGGER.md → LLM determines from assignment
        if not service_name:
            service_name = dagger_md_config.get("service_name", "")

        tools = dag.orchestrator_tools(
            gcloud=self.gcloud,
            project_id=self.project_id,
            region=self.region,
            credentials=self.credentials,
            oidc_token=self.oidc_token,
            workload_identity_provider=self.workload_identity_provider,
            service_account_email=self.service_account_email,
            developer_knowledge_api_key=self.developer_knowledge_api_key,
        )

        env = (
            dag.env()
            .with_string_input("assignment", assignment, "The deployment task to accomplish")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region to deploy to")
            .with_orchestrator_tools_input("tools", tools, "GCP deployment and operations tools")
        )

        if service_name:
            env = env.with_string_input("service_name", service_name, "The target service name")
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
        issue: Annotated[str, Doc("Description of the issue to diagnose")],
        source: Annotated[dagger.Directory | None, Doc("Source directory (optional, for DAGGER.md context)")] = None,
        service_name: Annotated[str, Doc("Service name to troubleshoot (optional, LLM reads from DAGGER.md or issue)")] = "",
    ) -> str:
        """Troubleshoot a GCP service using an AI agent.

        The agent checks the service status, reads logs, and provides
        a diagnosis with recommended actions. Supports Cloud Run,
        Firebase, and Vertex AI services.
        If the source directory contains a DAGGER.md file, it will be used
        as additional context for the agent.
        """
        dagger_md_config = await self._resolve_all(source)

        # service_name priority: explicit arg → DAGGER.md → LLM determines from issue
        if not service_name:
            service_name = dagger_md_config.get("service_name", "")

        tools = dag.orchestrator_tools(
            gcloud=self.gcloud,
            project_id=self.project_id,
            region=self.region,
            credentials=self.credentials,
            oidc_token=self.oidc_token,
            workload_identity_provider=self.workload_identity_provider,
            service_account_email=self.service_account_email,
            developer_knowledge_api_key=self.developer_knowledge_api_key,
        )

        env = (
            dag.env()
            .with_string_input("issue", issue, "The issue description to diagnose")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region")
            .with_orchestrator_tools_input("tools", tools, "GCP tools for diagnosis")
        )

        if service_name:
            env = env.with_string_input("service_name", service_name, "The service to troubleshoot")

        env = env.with_string_output("result", "Diagnosis and recommended actions")

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
