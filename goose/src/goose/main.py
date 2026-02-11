"""Goose — AI-powered GCP deployment, troubleshooting, and operations agent."""

import json
from typing import Annotated

import dagger
from dagger import Doc, dag, field, function, object_type


@object_type
class Goose:
    """AI-powered GCP deployment, troubleshooting, and operations agent.

    Supports Cloud Run, Firebase Hosting, Vertex AI, Artifact Registry,
    and health checks. Provides workspace tools for reading, editing,
    and searching deployment configs.

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

    # Optional: source directory for workspace tools
    source: Annotated[dagger.Directory | None, Doc("Source directory for workspace operations")] = field(default=None)

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
    # Priority order: explicit args -> DAGGER.md -> gcloud config -> defaults

    async def _resolve_project_id_early(self) -> str:
        """Resolve project_id without needing a gcloud container.

        Used when building gcloud from OIDC (which requires project_id).
        Checks: explicit -> DAGGER.md -> SA JSON -> error.
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
        """Resolve project_id: explicit -> DAGGER.md -> gcloud config -> error."""
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
        """Resolve region: explicit -> DAGGER.md -> gcloud config -> default us-central1."""
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

        Priority order: explicit args -> DAGGER.md -> gcloud config -> defaults.
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
        return dag.current_module().source().file(f"src/goose/prompts/{filename}")

    async def _read_context_file(self, source: dagger.Directory | None = None) -> str:
        """Read per-repo context from GOOSE.md, DAGGER.md, AGENT.md, or CLAUDE.md."""
        target = source or self.source
        if not target:
            return ""
        entries = await target.entries()
        for name in ("GOOSE.md", "DAGGER.md", "AGENT.md", "CLAUDE.md"):
            if name in entries:
                contents = await target.file(name).contents()
                return f"\n\n## Project Context (from {name})\n\n{contents}"
        return ""

    async def _build_llm(
        self,
        env: dagger.Env,
        prompt_file: str,
        source: dagger.Directory | None = None,
    ) -> dagger.LLM:
        """Build an LLM with the environment, current module tools, and prompts."""
        context_md = await self._read_context_file(source)
        system_prompt = await self._load_prompt("system_prompt.md").contents()

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(system_prompt + context_md)
        )

        return (
            llm
            .with_blocked_function("Goose", "assist")
            .with_blocked_function("Goose", "review")
            .with_blocked_function("Goose", "deploy")
            .with_blocked_function("Goose", "troubleshoot")
            .with_blocked_function("Goose", "upgrade")
            .with_blocked_function("Goose", "develop_github_issue")
            .with_prompt_file(self._load_prompt(prompt_file))
        )

    # --- Agent entrypoints ---

    @function
    async def assist(
        self,
        assignment: Annotated[str, Doc("What you want the agent to do (e.g. 'Inspect Cloud Run services and report their status')")],
        source: Annotated[dagger.Directory | None, Doc("Source directory for context (Dockerfiles, configs, DAGGER.md)")] = None,
    ) -> str:
        """General GCP operations assistant.

        Inspects infrastructure, plans deployments, answers questions about
        GCP services, and reviews configurations. Uses workspace tools to
        read deployment configs (Dockerfiles, firebase.json, cloudbuild.yaml).
        """
        dagger_md_config = await self._resolve_all(source)

        env = (
            dag.env()
            .with_string_input("assignment", assignment, "The operations task to accomplish")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region")
            .with_string_output("result", "The assistant's response")
        )

        if source:
            self.source = source
            env = env.with_workspace(source)

        work = await self._build_llm(env, "assist_prompt.md", source)
        return await work.env().output("result").as_string()

    @function
    async def review(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with deployment configs to review")],
        focus: Annotated[str, Doc("Specific area to focus the review on (optional)")] = "",
    ) -> str:
        """Review deployment configs for best practices and security.

        Examines Dockerfiles, firebase.json, cloudbuild.yaml, Cloud Run
        service YAML, IAM policies, and other GCP configs. Provides
        structured feedback with issues and recommendations.
        """
        dagger_md_config = await self._resolve_all(source)
        self.source = source

        env = (
            dag.env()
            .with_workspace(source)
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region")
            .with_string_output("result", "The review result")
        )

        if focus:
            env = env.with_string_input("focus", focus, "Specific area to focus the review on")

        work = await self._build_llm(env, "review_prompt.md", source)
        return await work.env().output("result").as_string()

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

        if not service_name:
            service_name = dagger_md_config.get("service_name", "")

        if source:
            self.source = source

        env = (
            dag.env()
            .with_string_input("assignment", assignment, "The deployment task to accomplish")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region to deploy to")
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
        """
        dagger_md_config = await self._resolve_all(source)

        if not service_name:
            service_name = dagger_md_config.get("service_name", "")

        if source:
            self.source = source

        env = (
            dag.env()
            .with_string_input("issue", issue, "The issue description to diagnose")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region")
        )

        if service_name:
            env = env.with_string_input("service_name", service_name, "The service to troubleshoot")

        env = env.with_string_output("result", "Diagnosis and recommended actions")

        work = await self._build_llm(env, "troubleshoot_prompt.md", source)
        return await work.env().output("result").as_string()

    @function
    async def upgrade(
        self,
        service_name: Annotated[str, Doc("Service to upgrade")],
        target_version: Annotated[str, Doc("Target version, image tag, or config change")] = "",
        source: Annotated[dagger.Directory | None, Doc("Source directory (optional, for context)")] = None,
        dry_run: Annotated[bool, Doc("Analyze and report changes without applying")] = False,
    ) -> str:
        """Upgrade a GCP service version, configuration, or traffic split.

        Inspects the current state, plans the upgrade, and applies changes.
        Supports Cloud Run image updates, traffic splitting, config changes,
        and Firebase redeployments.
        """
        dagger_md_config = await self._resolve_all(source)

        if source:
            self.source = source

        env = (
            dag.env()
            .with_string_input("service_name", service_name, "Service to upgrade")
            .with_string_input("project_id", self.project_id, "The GCP project ID")
            .with_string_input("region", self.region, "The GCP region")
            .with_string_output("result", "Upgrade result")
        )

        if target_version:
            env = env.with_string_input("target_version", target_version, "Target version or image tag")
        if source:
            env = env.with_workspace(source)
        if dry_run:
            env = env.with_string_input("dry_run", "true", "Only analyze and report, do not apply changes")

        work = await self._build_llm(env, "upgrade_prompt.md", source)
        return await work.env().output("result").as_string()

    # --- GitHub integration ---

    @function
    async def develop_github_issue(
        self,
        github_token: Annotated[dagger.Secret, Doc("GitHub token with repo and pull-request permissions")],
        issue_id: Annotated[int, Doc("GitHub issue number")],
        repository: Annotated[str, Doc("GitHub repository URL (e.g. 'https://github.com/owner/repo')")],
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
        base: Annotated[str, Doc("Base branch for the pull request")] = "main",
    ) -> str:
        """Read a GitHub issue, route it to the best function, and create a Pull Request.

        A router LLM reads the issue and selects the optimal function — assist,
        deploy, troubleshoot, or upgrade — then calls it with extracted parameters.
        Comments on the issue with a summary and a link to the PR.
        Returns the PR URL.
        """
        workspace = source or self.source
        gh = dag.github_issue(token=github_token)

        issue = gh.read(repository, issue_id)
        title = await issue.title()
        body = await issue.body()
        url = await issue.url()

        router_prompt = await self._load_prompt("router_prompt.md").contents()

        router_env = (
            dag.env()
            .with_string_input("issue_title", title, "The GitHub issue title")
            .with_string_input("issue_body", body, "The GitHub issue body")
            .with_string_output("function_name", "The function to call: assist, deploy, troubleshoot, or upgrade")
            .with_string_output("params_json", "JSON object with function parameters")
        )

        router = (
            dag.llm()
            .with_env(router_env)
            .with_system_prompt(router_prompt)
            .with_prompt(f"## GitHub Issue: {title}\n\n{body}")
        )

        function_name = await router.env().output("function_name").as_string()
        params_json = await router.env().output("params_json").as_string()
        params = json.loads(params_json)

        if function_name == "deploy":
            result = await self.deploy(source=workspace, **params)
        elif function_name == "troubleshoot":
            result = await self.troubleshoot(source=workspace, **params)
        elif function_name == "upgrade":
            result = await self.upgrade(source=workspace, **params)
        else:
            result = await self.assist(assignment=body, source=workspace)

        # For functions that return str, create a minimal directory for the PR
        pr_body = f"{body}\n\nCloses {url}\n\nAgent result:\n{result}"
        if workspace:
            pr_source = workspace
        else:
            pr_source = dag.directory()

        pr = gh.create_pull_request(
            repo=repository,
            title=title,
            body=pr_body,
            source=pr_source,
            base=base,
        )
        pr_url = await pr.url()

        await gh.write_comment(
            repo=repository,
            issue_id=issue_id,
            body=f"I've analyzed this issue and opened a pull request: {pr_url}",
        )

        return pr_url

    # --- Sub-agent ---

    @function
    async def task(
        self,
        description: Annotated[str, Doc("Short description of the sub-task")],
        prompt: Annotated[str, Doc("Detailed prompt for the sub-agent")],
    ) -> str:
        """Launch a sub-agent for research or focused work.

        The sub-agent has read-only access to the workspace and GCP tools.
        Use this for research, analysis, or exploring infrastructure state.
        """
        task_system = await self._load_prompt("task_system_prompt.md").contents()
        context_md = await self._read_context_file()

        env = (
            dag.env()
            .with_string_input("task_description", description, "The sub-task description")
            .with_string_input("task_prompt", prompt, "Detailed instructions for the sub-task")
            .with_string_output("result", "The sub-task result")
        )

        if self.source:
            env = env.with_workspace(self.source)

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(task_system + context_md)
            .with_blocked_function("Goose", "assist")
            .with_blocked_function("Goose", "review")
            .with_blocked_function("Goose", "deploy")
            .with_blocked_function("Goose", "troubleshoot")
            .with_blocked_function("Goose", "upgrade")
            .with_blocked_function("Goose", "develop_github_issue")
            .with_blocked_function("Goose", "task")
            .with_prompt(f"## Task: {description}\n\n{prompt}")
        )

        return await llm.env().output("result").as_string()

    # --- Workspace tools (exposed to LLM via with_current_module) ---

    @function
    async def read_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        offset: Annotated[int, Doc("Line number to start reading from (1-based)")] = 0,
        limit: Annotated[int, Doc("Maximum number of lines to read")] = 0,
    ) -> str:
        """Read a file from the workspace with line numbers."""
        if not self.source:
            raise ValueError("No source directory available. Pass --source to use workspace tools.")
        contents = await self.source.file(file_path).contents()
        lines = contents.splitlines()

        if offset > 0:
            lines = lines[offset - 1:]
        if limit > 0:
            lines = lines[:limit]

        start = offset if offset > 0 else 1
        numbered = [f"{start + i:4d}  {line}" for i, line in enumerate(lines)]
        return "\n".join(numbered)

    @function
    async def edit_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        old_string: Annotated[str, Doc("The exact string to find and replace")],
        new_string: Annotated[str, Doc("The replacement string")],
        replace_all: Annotated[bool, Doc("Replace all occurrences (default: first only)")] = False,
    ) -> dagger.Changeset:
        """Edit a file by replacing a string. The old_string must match exactly.

        Returns a changeset showing the diff.
        """
        if not self.source:
            raise ValueError("No source directory available. Pass --source to use workspace tools.")
        before = self.source
        contents = await before.file(file_path).contents()

        if old_string not in contents:
            msg = f"old_string not found in {file_path}"
            raise ValueError(msg)

        if replace_all:
            new_contents = contents.replace(old_string, new_string)
        else:
            new_contents = contents.replace(old_string, new_string, 1)

        after = before.with_new_file(file_path, new_contents)
        self.source = after
        return after.changes(before)

    @function
    async def write_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        contents: Annotated[str, Doc("The full file contents to write")],
    ) -> dagger.Changeset:
        """Create or overwrite a file in the workspace.

        Returns a changeset showing the diff.
        """
        if not self.source:
            raise ValueError("No source directory available. Pass --source to use workspace tools.")
        before = self.source
        after = before.with_new_file(file_path, contents)
        self.source = after
        return after.changes(before)

    @function
    async def glob(
        self,
        pattern: Annotated[str, Doc("Glob pattern (e.g. '**/*.py', '**/*.yaml')")],
    ) -> str:
        """Find files in the workspace matching a glob pattern."""
        if not self.source:
            raise ValueError("No source directory available. Pass --source to use workspace tools.")
        entries = await self.source.glob(pattern)
        if not entries:
            return "No files matched the pattern."
        return "\n".join(entries)

    @function
    async def grep(
        self,
        pattern: Annotated[str, Doc("Search pattern (regex supported)")],
        paths: Annotated[str, Doc("Comma-separated paths to search in (optional)")] = "",
        file_glob: Annotated[str, Doc("Glob pattern to filter files (e.g. '*.py')")] = "",
        insensitive: Annotated[bool, Doc("Case-insensitive search")] = False,
        limit: Annotated[int, Doc("Maximum number of matching lines to return")] = 100,
    ) -> str:
        """Search file contents in the workspace using grep."""
        if not self.source:
            raise ValueError("No source directory available. Pass --source to use workspace tools.")
        cmd = ["grep", "-rn"]
        if insensitive:
            cmd.append("-i")

        if file_glob:
            cmd.extend(["--include", file_glob])

        cmd.append(pattern)

        if paths:
            cmd.extend(paths.split(","))
        else:
            cmd.append(".")

        result = await (
            dag.container()
            .from_("alpine:latest")
            .with_mounted_directory("/work", self.source)
            .with_workdir("/work")
            .with_exec(cmd, expect=dagger.ExecExpect.ANY)
            .stdout()
        )

        lines = result.strip().splitlines()
        if limit > 0 and len(lines) > limit:
            lines = lines[:limit]
            lines.append(f"... (truncated, {limit} of many matches shown)")

        return "\n".join(lines) if lines else "No matches found."

    # --- GCP diagnostic utilities (exposed to LLM via with_current_module) ---

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

    # --- Cloud Run tools (absorbed from orchestrator-tools) ---

    @function
    async def deploy_service(
        self,
        image: Annotated[str, Doc("Container image URI to deploy")],
        service_name: Annotated[str, Doc("Cloud Run service name")],
        allow_unauthenticated: Annotated[bool, Doc("Allow public access")] = False,
        port: Annotated[int, Doc("Container port")] = 8080,
        cpu: Annotated[str, Doc("CPU allocation (e.g. '1', '2')")] = "1",
        memory: Annotated[str, Doc("Memory allocation (e.g. '512Mi', '1Gi')")] = "512Mi",
        min_instances: Annotated[int, Doc("Minimum instances (0 for scale-to-zero)")] = 0,
        max_instances: Annotated[int, Doc("Maximum instances")] = 10,
        env_vars: Annotated[list[str], Doc("Environment variables as KEY=VALUE")] = [],
    ) -> str:
        """Deploy a container image to Cloud Run as a service."""
        return await (
            dag.gcp_cloud_run()
            .service()
            .deploy(
                gcloud=self.gcloud,
                image=image,
                service_name=service_name,
                region=self.region,
                allow_unauthenticated=allow_unauthenticated,
                port=port,
                cpu=cpu,
                memory=memory,
                min_instances=min_instances,
                max_instances=max_instances,
                env_vars=env_vars,
            )
        )

    @function
    async def delete_service(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name to delete")],
    ) -> str:
        """Delete a Cloud Run service."""
        return await (
            dag.gcp_cloud_run()
            .service()
            .delete(
                gcloud=self.gcloud,
                service_name=service_name,
                region=self.region,
            )
        )

    @function
    async def get_service_url(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name")],
    ) -> str:
        """Get the URL of a deployed Cloud Run service."""
        return await (
            dag.gcp_cloud_run()
            .service()
            .get_url(
                gcloud=self.gcloud,
                service_name=service_name,
                region=self.region,
            )
        )

    @function
    async def service_exists(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name to check")],
    ) -> bool:
        """Check if a Cloud Run service exists."""
        return await (
            dag.gcp_cloud_run()
            .service()
            .exists(
                gcloud=self.gcloud,
                service_name=service_name,
                region=self.region,
            )
        )

    @function
    async def get_service_logs(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name")],
        limit: Annotated[int, Doc("Maximum number of log entries")] = 50,
        log_filter: Annotated[str, Doc("Log filter (e.g. 'severity>=ERROR')")] = "",
    ) -> str:
        """Get logs from a Cloud Run service."""
        return await (
            dag.gcp_cloud_run()
            .service()
            .get_logs(
                gcloud=self.gcloud,
                service_name=service_name,
                region=self.region,
                limit=limit,
                log_filter=log_filter,
            )
        )

    # --- Artifact Registry tools ---

    @function
    async def publish_container(
        self,
        container: Annotated[dagger.Container, Doc("Container to publish")],
        repository: Annotated[str, Doc("Artifact Registry repository name")],
        image_name: Annotated[str, Doc("Image name in the repository")],
        tag: Annotated[str, Doc("Image tag")] = "latest",
    ) -> str:
        """Publish a container image to Artifact Registry."""
        return await (
            dag.gcp_artifact_registry()
            .publish(
                container=container,
                project_id=self.project_id,
                repository=repository,
                image_name=image_name,
                region=self.region,
                tag=tag,
                gcloud=self.gcloud,
            )
        )

    @function
    async def list_images(
        self,
        repository: Annotated[str, Doc("Artifact Registry repository name")],
    ) -> str:
        """List images in an Artifact Registry repository."""
        return await (
            dag.gcp_artifact_registry()
            .list_images(
                gcloud=self.gcloud,
                project_id=self.project_id,
                repository=repository,
                region=self.region,
            )
        )

    # --- Firebase Hosting tools ---

    def _firebase_auth_kwargs(self) -> dict:
        """Build authentication kwargs for gcp-firebase calls."""
        if self.oidc_token and self.workload_identity_provider:
            kwargs: dict = {
                "oidc_token": self.oidc_token,
                "workload_identity_provider": self.workload_identity_provider,
            }
            if self.service_account_email:
                kwargs["service_account_email"] = self.service_account_email
            return kwargs
        if self.credentials:
            return {"credentials": self.credentials}
        raise ValueError(
            "Firebase operations require authentication. Provide either:\n"
            "  - oidc_token + workload_identity_provider (recommended for CI/CD)\n"
            "  - credentials (service account JSON key)"
        )

    @function
    async def deploy_firebase_hosting(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        build_command: Annotated[str, Doc("Build command (empty string to skip build for pre-built sources)")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
    ) -> str:
        """Deploy a web application to Firebase Hosting."""
        return await (
            dag.gcp_firebase()
            .deploy(
                project_id=self.project_id,
                source=source,
                build_command=build_command,
                node_version=node_version,
                **self._firebase_auth_kwargs(),
            )
        )

    @function
    async def deploy_firebase_preview(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        channel_id: Annotated[str, Doc("Preview channel ID (e.g. pr-123)")],
        build_command: Annotated[str, Doc("Build command (empty string to skip build for pre-built sources)")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        expires: Annotated[str, Doc("Channel expiration (e.g. '7d')")] = "7d",
    ) -> str:
        """Deploy to a Firebase Hosting preview channel. Returns the preview URL."""
        return await (
            dag.gcp_firebase()
            .deploy_preview(
                project_id=self.project_id,
                channel_id=channel_id,
                source=source,
                build_command=build_command,
                node_version=node_version,
                expires=expires,
                **self._firebase_auth_kwargs(),
            )
        )

    @function
    async def delete_firebase_channel(
        self,
        channel_id: Annotated[str, Doc("Preview channel ID to delete")],
    ) -> str:
        """Delete a Firebase Hosting preview channel."""
        return await (
            dag.gcp_firebase()
            .delete_channel(
                project_id=self.project_id,
                channel_id=channel_id,
                **self._firebase_auth_kwargs(),
            )
        )

    # --- Vertex AI tools ---

    @function
    async def deploy_vertex_model(
        self,
        image_uri: Annotated[str, Doc("Container image URI for the model")],
        model_name: Annotated[str, Doc("Model display name")],
        endpoint_name: Annotated[str, Doc("Endpoint display name")],
        machine_type: Annotated[str, Doc("VM machine type")] = "n1-standard-4",
        accelerator_type: Annotated[str, Doc("GPU type")] = "NVIDIA_TESLA_T4",
        accelerator_count: Annotated[int, Doc("Number of GPUs")] = 1,
        min_replicas: Annotated[int, Doc("Minimum replicas")] = 1,
        max_replicas: Annotated[int, Doc("Maximum replicas")] = 3,
    ) -> str:
        """Deploy a containerized ML model to Vertex AI."""
        return await (
            dag.gcp_vertex_ai()
            .deploy_model(
                gcloud=self.gcloud,
                image_uri=image_uri,
                model_name=model_name,
                endpoint_name=endpoint_name,
                region=self.region,
                machine_type=machine_type,
                accelerator_type=accelerator_type,
                accelerator_count=accelerator_count,
                min_replicas=min_replicas,
                max_replicas=max_replicas,
            )
        )

    @function
    async def list_vertex_models(self) -> str:
        """List all Vertex AI models in the project."""
        return await (
            dag.gcp_vertex_ai()
            .list_models(
                gcloud=self.gcloud,
                region=self.region,
            )
        )

    @function
    async def list_vertex_endpoints(self) -> str:
        """List all Vertex AI endpoints in the project."""
        return await (
            dag.gcp_vertex_ai()
            .list_endpoints(
                gcloud=self.gcloud,
                region=self.region,
            )
        )

    # --- Health Check tools ---

    @function
    async def check_http_health(
        self,
        container: Annotated[dagger.Container, Doc("Container to health check")],
        port: Annotated[int, Doc("Port number")] = 8080,
        path: Annotated[str, Doc("HTTP path")] = "/health",
        timeout: Annotated[int, Doc("Timeout in seconds")] = 60,
    ) -> dagger.Container:
        """Run an HTTP health check against a container. Returns the container if healthy."""
        return await (
            dag.health_check()
            .http(
                container=container,
                port=port,
                path=path,
                timeout=timeout,
            )
        )

    @function
    async def check_tcp_health(
        self,
        container: Annotated[dagger.Container, Doc("Container to health check")],
        port: Annotated[int, Doc("Port number")] = 8080,
        timeout: Annotated[int, Doc("Timeout in seconds")] = 60,
    ) -> dagger.Container:
        """Run a TCP health check against a container. Returns the container if port is open."""
        return await (
            dag.health_check()
            .tcp(
                container=container,
                port=port,
                timeout=timeout,
            )
        )

    # --- Google Developer Knowledge (GCP Docs Search) ---

    _DK_API_BASE = "https://developerknowledge.googleapis.com/v1alpha"

    def _require_dk_api_key(self) -> dagger.Secret:
        """Validate that the Developer Knowledge API key is available."""
        if self.developer_knowledge_api_key is None:
            raise ValueError(
                "GCP docs search requires 'developer_knowledge_api_key'. "
                "Pass the API key when constructing the agent."
            )
        return self.developer_knowledge_api_key

    def _dk_curl_container(self) -> dagger.Container:
        """Create a curl container with the Developer Knowledge API key."""
        return (
            dag.container()
            .from_("curlimages/curl:latest")
            .with_secret_variable("DK_API_KEY", self._require_dk_api_key())
        )

    @function
    async def search_gcp_docs(
        self,
        query: Annotated[str, Doc("Search query (e.g. 'How to configure Cloud Run VPC connector')")],
    ) -> str:
        """Search Google's official developer documentation for GCP, Firebase, Android, and more.

        Returns relevant documentation chunks with page references.
        Use get_gcp_doc with a parent value from results to retrieve full page content.
        """
        return await (
            self._dk_curl_container()
            .with_exec([
                "sh", "-c",
                'curl -sf -G'
                f' "{self._DK_API_BASE}/documents:searchDocumentChunks"'
                ' --data-urlencode "query=$0"'
                ' --data-urlencode "key=$DK_API_KEY"',
                query,
            ])
            .stdout()
        )

    @function
    async def get_gcp_doc(
        self,
        document_name: Annotated[str, Doc("Document resource name from search results (the 'parent' field)")],
    ) -> str:
        """Retrieve the full content of a Google developer documentation page.

        Use the 'parent' field from search_gcp_docs results as the document_name.
        Returns the full page as Markdown.
        """
        return await (
            self._dk_curl_container()
            .with_exec([
                "sh", "-c",
                f'curl -sf "{self._DK_API_BASE}/$0?key=$DK_API_KEY"',
                document_name,
            ])
            .stdout()
        )

    @function
    async def batch_get_gcp_docs(
        self,
        document_names: Annotated[list[str], Doc("List of document resource names (the 'parent' fields from search results)")],
    ) -> str:
        """Retrieve multiple Google developer documentation pages at once.

        Use the 'parent' fields from search_gcp_docs results as document names.
        Returns all pages as Markdown.
        """
        results = []
        for name in document_names:
            content = await (
                self._dk_curl_container()
                .with_exec([
                    "sh", "-c",
                    f'curl -sf "{self._DK_API_BASE}/$0?key=$DK_API_KEY"',
                    name,
                ])
                .stdout()
            )
            results.append(content)
        return "\n---\n".join(results)
