"""Goose — AI-powered GCP deployment, troubleshooting, and operations agent."""

import re
from typing import Annotated

import dagger
from dagger import Doc, dag, field, function, object_type

from agent_base import github_tools, llm_helpers, mcp_stdio, routing, workspace
from agent_base.mcp_stdio import McpServer

# Entrypoints blocked on all LLMs to prevent recursion
_BLOCKED_ENTRYPOINTS = [
    "assist", "review", "deploy", "troubleshoot",
    "upgrade", "develop_github_issue", "suggest_github_fix",
]

# Destructive tools blocked on read-only LLMs (review, suggest-fix, task sub-agent)
_BLOCKED_DESTRUCTIVE = [
    "deploy_service", "delete_service",
    "deploy_firebase_hosting", "deploy_firebase_preview", "delete_firebase_channel",
    "deploy_vertex_model",
    "edit_file", "write_file",
    "publish_container", "build_and_publish",
]

# Exposed fields are tools too in Dagger 1.0; hide them from the LLM
_FIELDS = [
    "gcloud", "oidc_token", "workload_identity_provider", "service_account_email",
    "credentials", "google_cloud_dir", "project_id", "region", "source",
    "self_improve", "developer_knowledge_api_key",
]

_DAGGER_CONFIG_FILE = "DAGGER.md"
_GOOSE_CONTEXT_FILE = "GOOSE.md"

_SELF_IMPROVE_PROMPT = """

## Self-Improvement Instructions

You have self-improvement enabled. As you work, record useful discoveries in
**two** context files. Use `readFile` to check each file's current contents
first, then use `editFile` to append new entries at the end. If a file does
not exist yet, use `writeFile` to create it.

### Agent-specific file: `{agent_file}`

Record knowledge specific to this agent's domain here:
- GCP service configurations and deployment patterns you discovered
- Infrastructure-specific gotchas (e.g. Cloud Run cold starts, Firebase quota limits)
- Authentication and IAM patterns for this project
- Service-specific version constraints or migration notes

### Shared file: `AGENTS.md`

Record general-purpose knowledge about the repository here:
- Project architecture and folder structure
- Cross-cutting conventions (naming, error handling, logging)
- CI/CD and deployment patterns
- Dependency management approach
- Team preferences expressed during this session

### Format rules

- Use markdown headings and bullet points
- Add entries under a `## Learned Context` heading at the bottom of each file
- Keep each entry to 1-3 lines
- Do not duplicate information already present in either file
- Do not record generic GCP knowledge, temporary state, or anything already documented

Do this as a **final step**, after completing your main task successfully.
"""


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

    # Self-improvement mode
    self_improve: Annotated[
        str,
        Doc("Self-improvement mode: 'off' (default), 'write' (update context file), 'commit' (update + git commit)"),
    ] = field(default="off")

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
        if _DAGGER_CONFIG_FILE not in entries:
            return {}
        contents = await source.file(_DAGGER_CONFIG_FILE).contents()

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
        self._resolved = True
        return self._dagger_md_config

    async def _ensure_resolved(self) -> None:
        """Resolve gcloud, project_id, and region for a tool call.

        The LLM's tools run on the object as the agent was constructed, before
        an entrypoint resolved anything, so each GCP tool resolves from the
        constructor arguments (and DAGGER.md in the constructor source).
        """
        if not getattr(self, "_resolved", False):
            await self._resolve_all(self.source)

    # --- MCP servers ---

    def _gcloud_mcp(self, gcloud: dagger.Container) -> McpServer:
        """The gcloud-mcp server.

        Built on top of the resolved gcloud container so it inherits
        authentication (OIDC, SA key, host gcloud, or pre-built).
        """
        return McpServer(
            name="gcloud",
            container=(
                gcloud
                .with_exec(["apk", "add", "--no-cache", "nodejs", "npm"])
                .with_mounted_cache("/root/.npm", dag.cache_volume("node-npm"))
                .with_exec(["npm", "install", "-g", "@google-cloud/gcloud-mcp"])
            ),
            command=["npx", "@google-cloud/gcloud-mcp"],
            # Calls read live cloud state: never reuse a cached answer
            live=True,
        )

    # --- Prompt helpers ---

    def _load_prompt(self, filename: str) -> dagger.File:
        """Load a prompt file from the module source."""
        return dag.current_module().source().file(f"src/goose/prompts/{filename}")

    async def _read_context_file(self, source: dagger.Directory | None = None) -> str:
        """Read per-repo context from agent-specific, shared, and DAGGER.md files."""
        target = source or self.source
        if not target:
            return ""
        return await llm_helpers.read_context_file(
            target, (_GOOSE_CONTEXT_FILE,), extra_read_files=(_DAGGER_CONFIG_FILE,),
        )

    _DOCS_SEARCH_SECTION = """

## GCP Documentation Search

You have access to `searchGcpDocs`, `getGcpDoc`, and `batchGetGcpDocs` to search Google's official developer documentation in real time. Use these when:

- You encounter an unfamiliar GCP configuration option or error message
- You need to verify the latest API syntax, flags, or default values
- Troubleshooting requires checking current documentation for known issues

Do not search docs for basic operations you already know how to perform.
"""

    # Tasks that need the gcloud MCP server. None = no MCP server.
    # deploy/review don't need MCP — deploy has deploy_service as a Dagger function,
    # review just reads files. Skipping MCP avoids 50s+ startup and tool noise.
    _TASK_NEEDS_MCP = {
        "assist": True,
        "troubleshoot": True,
        "upgrade": True,
        "deploy": False,
        "review": False,
        "suggest_fix": False,
    }

    def _blocked(self, *extra: str) -> list[str]:
        return [*_BLOCKED_ENTRYPOINTS, *_FIELDS, *extra]

    async def _build_llm(
        self,
        prompt_file: str,
        source: dagger.Directory | None = None,
        task: str = "assist",
        inputs: dict[str, str] | None = None,
        extra_blocked: tuple[str, ...] | list[str] = (),
    ) -> dagger.LLM:
        """Build an LLM bound to the source as its workspace, with this agent's tools and prompts."""
        context_md = await self._read_context_file(source)
        system_prompt = await self._load_prompt("system_prompt.md").contents()

        if self.developer_knowledge_api_key:
            system_prompt += self._DOCS_SEARCH_SECTION

        if self.self_improve != "off":
            system_prompt += _SELF_IMPROVE_PROMPT.format(agent_file=_GOOSE_CONTEXT_FILE)

        mcp_servers = [self._gcloud_mcp(self.gcloud)] if self._TASK_NEEDS_MCP.get(task, True) else []

        # Workspace tools need a workspace even when no source was given
        llm = (
            dag.llm()
            .with_workspace((source or dag.directory()).as_workspace())
            .with_tools(dag.current_node(), except_=llm_helpers.tool_exclusions(
                self._blocked(*extra_blocked, *mcp_stdio.blocked_tools(mcp_servers)),
            ))
        )
        llm, mcp_context = await mcp_stdio.attach(llm, mcp_servers)
        llm = llm.with_system_prompt(system_prompt + context_md + mcp_context)

        prompt = await self._load_prompt(prompt_file).contents()
        return llm.with_prompt(prompt + llm_helpers.format_inputs(inputs))

    async def _build_suggest_fix_llm(self, source: dagger.Directory | None, inputs: dict[str, str]) -> dagger.LLM:
        """Build a read-only LLM for suggest-github-fix (no MCP; suggestions come back in the reply)."""
        return await self._build_llm(
            "suggest_fix_prompt.md", source, task="suggest_fix", inputs=inputs,
            extra_blocked=["task", *_BLOCKED_DESTRUCTIVE],
        )

    def _gcp_inputs(self, **inputs: str) -> dict[str, str]:
        return {**inputs, "project_id": self.project_id, "region": self.region}

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
        await self._resolve_all(source)
        work = await self._build_llm(
            "assist_prompt.md", source, task="assist",
            inputs=self._gcp_inputs(assignment=assignment),
        )
        return await llm_helpers.reply(work)

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
        await self._resolve_all(source)
        work = await self._build_llm(
            "review_prompt.md", source, task="review",
            inputs=self._gcp_inputs(focus=focus),
            extra_blocked=_BLOCKED_DESTRUCTIVE,
        )
        return await llm_helpers.reply(work)

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

        # Fast path: if the assignment contains a container image URI and a
        # service name, call deploy_service directly instead of routing through
        # the LLM.  This avoids flaky LLM behavior for straightforward deploys.
        if not source and service_name:
            result = self._try_direct_cloud_run_deploy(assignment, service_name)
            if result is not None:
                return await result

        inputs = self._gcp_inputs(
            assignment=assignment,
            service_name=service_name,
            repository=repository,
        )
        if source:
            inputs["source"] = (
                "The source directory to build and deploy is the workspace: the workspace "
                "tools read it, and the Firebase deploy tools and buildAndPublish deploy it."
            )
        work = await self._build_llm("deploy_prompt.md", source, task="deploy", inputs=inputs)
        return await llm_helpers.reply(work)

    def _try_direct_cloud_run_deploy(self, assignment: str, service_name: str):
        """Attempt to parse a simple Cloud Run deploy from the assignment text.

        Returns an awaitable deploy result if the assignment specifies a
        container image URI, or None to fall back to the LLM.
        """
        # Match known container registry domains.  Full domains are
        # enumerated to avoid ambiguous quantifiers that could backtrack.
        _REGISTRY_RE = (
            r'((?:[\w-]+\.gcr\.io|gcr\.io|docker\.io'
            r'|[\w-]+\.pkg\.dev|ghcr\.io|docker\.com)'
            r'/[a-zA-Z0-9_./:@-]+)'
        )
        m = re.search(_REGISTRY_RE, assignment)
        if not m:
            return None

        image = m.group(1)
        allow_unauth = bool(re.search(
            r'(?:allow[_ ]unauthenticated|public[_ ]access|--allow-unauthenticated)',
            assignment, re.IGNORECASE,
        ))

        return self.deploy_service(
            image=image,
            service_name=service_name,
            allow_unauthenticated=allow_unauth,
        )

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

        work = await self._build_llm(
            "troubleshoot_prompt.md", source, task="troubleshoot",
            inputs=self._gcp_inputs(issue=issue, service_name=service_name),
        )
        return await llm_helpers.reply(work)

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
        await self._resolve_all(source)

        inputs = self._gcp_inputs(service_name=service_name, target_version=target_version)
        if dry_run:
            inputs["dry_run"] = "true — only analyze and report, do not apply changes"
        work = await self._build_llm("upgrade_prompt.md", source, task="upgrade", inputs=inputs)
        return await llm_helpers.reply(work)

    # --- GitHub integration ---

    @function
    async def suggest_github_fix(
        self,
        github_token: Annotated[dagger.Secret, Doc("GitHub token with repo permissions")],
        pr_number: Annotated[int, Doc("Pull request number")],
        repo: Annotated[str, Doc("GitHub repository URL (e.g. 'https://github.com/owner/repo')")],
        commit_sha: Annotated[str, Doc("HEAD commit SHA of the PR branch")],
        error_output: Annotated[str, Doc("CI error output (stderr/stdout)")],
        source: Annotated[dagger.Directory | None, Doc("Source directory of the PR branch")] = None,
    ) -> str:
        """Analyze a CI failure and post inline code suggestions on a GitHub PR.

        Reads the error output, explores source files, and posts GitHub
        "suggested changes" that developers can apply with one click.
        Does not require GCP authentication.
        """
        # Skip _resolve_all — GCP auth not needed for suggesting code fixes
        return await github_tools.suggest_github_fix_impl(
            self._build_suggest_fix_llm, github_token, pr_number, repo,
            commit_sha, error_output, source or self.source,
        )

    @function
    async def develop_github_issue(
        self,
        github_token: Annotated[dagger.Secret, Doc("GitHub token with repo and pull-request permissions")],
        issue_id: Annotated[int, Doc("GitHub issue number")],
        repository: Annotated[str, Doc("GitHub repository URL (e.g. 'https://github.com/owner/repo')")],
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
        base: Annotated[str, Doc("Base branch for the pull request")] = "main",
        suggest_github_fix_on_failure: Annotated[bool, Doc("Post a diagnostic comment on the issue if the agent fails")] = False,
    ) -> str:
        """Read a GitHub issue, route it to the best function, and create a Pull Request.

        A router LLM reads the issue and selects the optimal function — assist,
        deploy, troubleshoot, or upgrade — then calls it with extracted parameters.
        Comments on the issue with a summary and a link to the PR.
        Returns the PR URL.
        """
        workspace_dir = source or self.source
        gh = dag.github_issue(token=github_token)

        issue = gh.read(repository, issue_id)
        title = await issue.title()
        body = await issue.body()
        url = await issue.url()

        router_prompt = await self._load_prompt("router_prompt.md").contents()
        router = (
            dag.llm()
            .with_system_prompt(router_prompt)
            .with_prompt(f"## GitHub Issue: {title}\n\n{body}")
        )
        function_name, params = routing.parse_router_reply(await llm_helpers.reply(router))

        # Filter params to expected keys per function to prevent TypeErrors
        _allowed_keys = {
            "deploy": {"assignment", "service_name", "repository"},
            "troubleshoot": {"issue", "service_name"},
            "upgrade": {"service_name", "target_version"},
        }
        allowed = _allowed_keys.get(function_name, set())
        params = {k: v for k, v in params.items() if k in allowed}

        result = await self._execute_routed_function(
            function_name, params, body, workspace_dir,
            gh, repository, issue_id, suggest_github_fix_on_failure,
        )

        # For functions that return str, create a minimal directory for the PR
        pr_body = f"{body}\n\nCloses {url}\n\nAgent result:\n{result}"
        if workspace_dir:
            pr_source = workspace_dir
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

    async def _execute_routed_function(
        self,
        function_name: str,
        params: dict,
        body: str,
        workspace_dir: dagger.Directory | None,
        gh,
        repository: str,
        issue_id: int,
        suggest_on_failure: bool,
    ) -> str:
        """Dispatch to the routed function, posting a comment on failure if requested."""
        try:
            if function_name == "deploy":
                return await self.deploy(source=workspace_dir, **params)
            elif function_name == "troubleshoot":
                return await self.troubleshoot(source=workspace_dir, **params)
            elif function_name == "upgrade":
                return await self.upgrade(source=workspace_dir, **params)
            else:
                return await self.assist(assignment=body, source=workspace_dir)
        except Exception as exc:
            if suggest_on_failure:
                await gh.write_comment(
                    repo=repository,
                    issue_id=issue_id,
                    body=(
                        f"**Agent encountered an error:**\n\n"
                        f"**Function**: `{function_name}`\n"
                        f"**Error**:\n```\n{str(exc)[:3000]}\n```\n\n"
                        f"Run `suggest-github-fix` on the PR for inline code suggestions."
                    ),
                )
            raise

    # --- Sub-agent ---

    @function
    async def task(
        self,
        ws: dagger.Workspace,
        description: Annotated[str, Doc("Short description of the sub-task")],
        prompt: Annotated[str, Doc("Detailed prompt for the sub-agent")],
    ) -> str:
        """Launch a sub-agent for research or focused work.

        The sub-agent has read-only access to the workspace and GCP tools.
        Use this for research, analysis, or exploring infrastructure state.
        """
        task_system = await self._load_prompt("task_system_prompt.md").contents()
        context_md = await self._read_context_file()

        # Block entrypoints (prevent recursion), destructive tools (read-only
        # sub-agent) and the MCP tool (the sub-agent gets no MCP server)
        llm = (
            dag.llm()
            .with_workspace(ws)
            .with_tools(dag.current_node(), except_=llm_helpers.tool_exclusions(
                self._blocked("task", "mcp", *_BLOCKED_DESTRUCTIVE),
            ))
            .with_system_prompt(task_system + context_md)
            .with_prompt(f"## Task: {description}\n\n{prompt}")
        )
        return await llm_helpers.reply(llm)

    # --- Workspace tools ---

    @function
    async def read_file(
        self,
        ws: dagger.Workspace,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        offset: Annotated[int, Doc("Line number to start reading from (1-based)")] = 0,
        limit: Annotated[int, Doc("Maximum number of lines to read")] = 0,
    ) -> str:
        """Read a file from the workspace with line numbers."""
        return await workspace.read_file_impl(ws, file_path, offset, limit)

    @function
    async def edit_file(
        self,
        ws: dagger.Workspace,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        old_string: Annotated[str, Doc("The exact string to find and replace")],
        new_string: Annotated[str, Doc("The replacement string")],
        replace_all: Annotated[bool, Doc("Replace all occurrences (default: first only)")] = False,
    ) -> dagger.Workspace:
        """Edit a file by replacing a string. The old_string must match exactly.

        Returns the edited workspace.
        """
        return await workspace.edit_file_impl(ws, file_path, old_string, new_string, replace_all)

    @function
    def write_file(
        self,
        ws: dagger.Workspace,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        contents: Annotated[str, Doc("The full file contents to write")],
    ) -> dagger.Workspace:
        """Create or overwrite a file in the workspace.

        Returns the edited workspace.
        """
        return workspace.write_file_impl(ws, file_path, contents)

    @function
    async def glob(
        self,
        ws: dagger.Workspace,
        pattern: Annotated[str, Doc("Glob pattern (e.g. '**/*.py', '**/*.yaml')")],
    ) -> str:
        """Find files in the workspace matching a glob pattern."""
        return await workspace.glob_impl(ws, pattern)

    @function
    async def grep(
        self,
        ws: dagger.Workspace,
        pattern: Annotated[str, Doc("Search pattern (regex supported)")],
        paths: Annotated[str, Doc("Comma-separated paths to search in (optional)")] = "",
        file_glob: Annotated[str, Doc("Glob pattern to filter files (e.g. '*.py')")] = "",
        insensitive: Annotated[bool, Doc("Case-insensitive search")] = False,
        limit: Annotated[int, Doc("Maximum number of matching lines to return")] = 100,
    ) -> str:
        """Search file contents in the workspace using grep."""
        return await workspace.grep_impl(ws, pattern, paths, file_glob, insensitive, limit)

    @function
    async def mcp(
        self,
        server: Annotated[str, Doc("MCP server name, as listed in the system prompt (e.g. 'gcloud')")],
        tool: Annotated[str, Doc("Name of the server's tool to call")],
        arguments: Annotated[str, Doc("The tool's arguments, as a JSON object")] = "{}",
    ) -> str:
        """Call a tool of one of the MCP servers listed in the system prompt."""
        if server != "gcloud":
            raise ValueError(f"unknown MCP server {server!r}; the server is 'gcloud'")
        await self._ensure_resolved()
        return await mcp_stdio.call(self._gcloud_mcp(self.gcloud), tool, arguments)

    # --- GCP diagnostic utilities ---

    @function
    async def describe_service(
        self,
        service_name: Annotated[str, Doc("Cloud Run service name")],
    ) -> str:
        """Get the full configuration of a Cloud Run service as JSON."""
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
    async def build_and_publish(
        self,
        ws: dagger.Workspace,
        repository: Annotated[str, Doc("Artifact Registry repository name")],
        image_name: Annotated[str, Doc("Image name in the repository")],
        tag: Annotated[str, Doc("Image tag")] = "latest",
        dockerfile: Annotated[str, Doc("Dockerfile path, relative to the workspace")] = "Dockerfile",
    ) -> str:
        """Build the workspace with its Dockerfile and publish the image to Artifact Registry.

        Returns the published image reference, ready for deployService.
        """
        await self._ensure_resolved()
        container = ws.directory(".").docker_build(dockerfile=dockerfile)
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
        await self._ensure_resolved()
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
        ws: dagger.Workspace,
        build_command: Annotated[str, Doc("Build command (empty string to skip build for pre-built sources)")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
    ) -> str:
        """Deploy the web application in the workspace (with its firebase.json) to Firebase Hosting."""
        await self._ensure_resolved()
        return await (
            dag.gcp_firebase()
            .deploy(
                project_id=self.project_id,
                source=ws.directory("."),
                build_command=build_command,
                node_version=node_version,
                **self._firebase_auth_kwargs(),
            )
        )

    @function
    async def deploy_firebase_preview(
        self,
        ws: dagger.Workspace,
        channel_id: Annotated[str, Doc("Preview channel ID (e.g. pr-123)")],
        build_command: Annotated[str, Doc("Build command (empty string to skip build for pre-built sources)")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        expires: Annotated[str, Doc("Channel expiration (e.g. '7d')")] = "7d",
    ) -> str:
        """Deploy the workspace (with its firebase.json) to a Firebase Hosting preview channel.

        Returns the preview URL.
        """
        await self._ensure_resolved()
        return await (
            dag.gcp_firebase()
            .deploy_preview(
                project_id=self.project_id,
                channel_id=channel_id,
                source=ws.directory("."),
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        await self._ensure_resolved()
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
        Use getGcpDoc with a parent value from results to retrieve full page content.
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

        Use the 'parent' field from searchGcpDocs results as the document name.
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

        Use the 'parent' fields from searchGcpDocs results as document names.
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
