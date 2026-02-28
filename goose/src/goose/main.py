"""Goose — AI-powered GCP deployment, troubleshooting, and operations agent."""

import json
import re
from typing import Annotated

import dagger
from dagger import Doc, dag, field, function, object_type


async def _get_result_or_last_reply(work: dagger.LLM, output_name: str = "result") -> str:
    """Get a string output from the LLM, falling back to last_reply.

    Some LLMs produce text output without calling the output binding tool.
    This tries the binding first, then falls back to the LLM's last reply.
    """
    try:
        value = await work.env().output(output_name).as_string()
        if value and value.strip():
            return value
    except Exception:
        pass
    return await work.last_reply()

# Entrypoints blocked on all LLMs to prevent recursion
_BLOCKED_ENTRYPOINTS = [
    "assist", "review", "deploy", "troubleshoot",
    "upgrade", "develop_github_issue", "suggest_github_fix",
]


def _parse_router_response(params_json: str | None) -> tuple[dict, str | None]:
    """Parse JSON from router LLM output with fallback for malformed responses.

    Returns (params_dict, fallback_function_name). fallback_function_name is
    "assist" if parsing failed entirely, None if parsing succeeded.
    """
    try:
        return json.loads(params_json), None
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{[^}]*\}", params_json or "")
        if match:
            try:
                return json.loads(match.group()), None
            except json.JSONDecodeError:
                return {}, "assist"
        return {}, "assist"

# Destructive tools blocked on the read-only sub-agent
_BLOCKED_DESTRUCTIVE = [
    "deploy_service", "delete_service",
    "deploy_firebase_hosting", "deploy_firebase_preview", "delete_firebase_channel",
    "deploy_vertex_model",
    "edit_file", "write_file",
    "publish_container",
    "suggest_github_pr_code_comment",
]

_DAGGER_CONFIG_FILE = "DAGGER.md"
_GOOSE_CONTEXT_FILE = "GOOSE.md"
_TRUNCATION_NOTICE = "\n\n[Truncated.]"

_SELF_IMPROVE_PROMPT = """

## Self-Improvement Instructions

You have self-improvement enabled. As you work, record useful discoveries in
**two** context files. Use `read_file` to check each file's current contents
first, then use `edit_file` to append new entries at the end. If a file does
not exist yet, use `write_file` to create it.

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
_DOC_GCP_PROJECT_ID = "The GCP project ID"
_DOC_GCP_REGION = "The GCP region"
_ERROR_NO_SOURCE_DIR = "No source directory available. Pass --source to use workspace tools."


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

    # Private fields set during suggest_github_fix execution
    _github_token: dagger.Secret | None = field(default=None, init=False)
    _pr_repo: str = field(default="", init=False)
    _pr_number: int = field(default=0, init=False)
    _pr_commit_sha: str = field(default="", init=False)

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
        return self._dagger_md_config

    # --- MCP servers ---

    def _gcloud_mcp_service(self, gcloud: dagger.Container) -> dagger.Service:
        """Create the gcloud-mcp server as a Dagger Service.

        Built on top of the resolved gcloud container so it inherits
        authentication (OIDC, SA key, host gcloud, or pre-built).
        """
        return (
            gcloud
            .with_exec(["apk", "add", "--no-cache", "nodejs", "npm"])
            .with_mounted_cache("/root/.npm", dag.cache_volume("node-npm"))
            .with_exec(["npm", "install", "-g", "@google-cloud/gcloud-mcp"])
            .with_default_args(["npx", "@google-cloud/gcloud-mcp"])
            .as_service()
        )

    # --- Prompt helpers ---

    def _load_prompt(self, filename: str) -> dagger.File:
        """Load a prompt file from the module source."""
        return dag.current_module().source().file(f"src/goose/prompts/{filename}")

    _MAX_CONTEXT_CHARS = 4000  # ~1000 tokens — keeps total prompt under budget

    # Shared file names — read in order, first match used as shared context
    _SHARED_CONTEXT_FILES = ("AGENTS.md", "AGENT.md", "CLAUDE.md")

    async def _read_context_section(
        self, target: dagger.Directory, name: str,
    ) -> str:
        """Read a single context file and return a formatted section."""
        contents = await target.file(name).contents()
        if len(contents) > self._MAX_CONTEXT_CHARS:
            contents = contents[:self._MAX_CONTEXT_CHARS] + _TRUNCATION_NOTICE
        return f"## Project Context (from {name})\n\n{contents}"

    async def _read_context_file(self, source: dagger.Directory | None = None) -> str:
        """Read per-repo context from agent-specific, shared, and DAGGER.md files."""
        target = source or self.source
        if not target:
            return ""
        entries = await target.entries()
        sections: list[str] = []

        # 1. Agent-specific file
        if _GOOSE_CONTEXT_FILE in entries:
            sections.append(await self._read_context_section(target, _GOOSE_CONTEXT_FILE))

        # 2. Shared file (AGENTS.md > AGENT.md > CLAUDE.md)
        for name in self._SHARED_CONTEXT_FILES:
            if name in entries:
                sections.append(await self._read_context_section(target, name))
                break

        # 3. DAGGER.md (extra context for GCP/Dagger config)
        if _DAGGER_CONFIG_FILE in entries:
            sections.append(await self._read_context_section(target, _DAGGER_CONFIG_FILE))

        return "\n\n" + "\n\n".join(sections) if sections else ""

    _DOCS_SEARCH_SECTION = """

## GCP Documentation Search

You have access to `search_gcp_docs`, `get_gcp_doc`, and `batch_get_gcp_docs` to search Google's official developer documentation in real time. Use these when:

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
    }

    async def _build_llm(
        self,
        env: dagger.Env,
        prompt_file: str,
        source: dagger.Directory | None = None,
        task: str = "assist",
    ) -> dagger.LLM:
        """Build an LLM with the environment, current module tools, and prompts."""
        context_md = await self._read_context_file(source)
        system_prompt = await self._load_prompt("system_prompt.md").contents()

        if self.developer_knowledge_api_key:
            system_prompt += self._DOCS_SEARCH_SECTION

        if self.self_improve != "off":
            system_prompt += _SELF_IMPROVE_PROMPT.format(agent_file=_GOOSE_CONTEXT_FILE)

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(system_prompt + context_md)
        )

        if self._TASK_NEEDS_MCP.get(task, True):
            llm = llm.with_mcp_server("gcloud", self._gcloud_mcp_service(self.gcloud))

        for fn in _BLOCKED_ENTRYPOINTS:
            llm = llm.with_blocked_function("Goose", fn)

        return llm.with_prompt_file(self._load_prompt(prompt_file))

    async def _build_suggest_fix_llm(
        self,
        env: dagger.Env,
        source: dagger.Directory | None = None,
    ) -> dagger.LLM:
        """Build an LLM for suggest-github-fix (no MCP servers, workspace + suggestion tool)."""
        context_md = await self._read_context_file(source)
        system_prompt = await self._load_prompt("system_prompt.md").contents()

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(system_prompt + context_md)
        )

        for fn in _BLOCKED_ENTRYPOINTS + ["task"] + _BLOCKED_DESTRUCTIVE:
            if fn != "suggest_github_pr_code_comment":
                llm = llm.with_blocked_function("Goose", fn)

        return llm.with_prompt_file(self._load_prompt("suggest_fix_prompt.md"))

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

        env = (
            dag.env()
            .with_string_input("assignment", assignment, "The operations task to accomplish")
            .with_string_input("project_id", self.project_id, _DOC_GCP_PROJECT_ID)
            .with_string_input("region", self.region, _DOC_GCP_REGION)
            .with_string_output("result", "The assistant's response")
        )

        if source:
            self.source = source
            env = env.with_workspace(source)

        work = await self._build_llm(env, "assist_prompt.md", source)
        return await _get_result_or_last_reply(work)

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
        self.source = source

        env = (
            dag.env()
            .with_workspace(source)
            .with_string_input("project_id", self.project_id, _DOC_GCP_PROJECT_ID)
            .with_string_input("region", self.region, _DOC_GCP_REGION)
            .with_string_output("result", "The review result")
        )

        if focus:
            env = env.with_string_input("focus", focus, "Specific area to focus the review on")

        work = await self._build_llm(env, "review_prompt.md", source, task="review")
        return await _get_result_or_last_reply(work)

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

        # Fast path: if the assignment contains a container image URI and a
        # service name, call deploy_service directly instead of routing through
        # the LLM.  This avoids flaky LLM behavior for straightforward deploys.
        if not source and service_name:
            result = self._try_direct_cloud_run_deploy(assignment, service_name)
            if result is not None:
                return await result

        env = (
            dag.env()
            .with_string_input("assignment", assignment, "The deployment task to accomplish")
            .with_string_input("project_id", self.project_id, _DOC_GCP_PROJECT_ID)
            .with_string_input("region", self.region, "The GCP region to deploy to")
        )

        if service_name:
            env = env.with_string_input("service_name", service_name, "The target service name")
        if source:
            env = env.with_directory_input("source", source, "Source code directory to build")
        if repository:
            env = env.with_string_input("repository", repository, "Artifact Registry repository name")

        env = env.with_string_output("result", "The deployment result including the service URL or error details")

        work = await self._build_llm(env, "deploy_prompt.md", source, task="deploy")
        return await _get_result_or_last_reply(work)

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

        if source:
            self.source = source

        env = (
            dag.env()
            .with_string_input("issue", issue, "The issue description to diagnose")
            .with_string_input("project_id", self.project_id, _DOC_GCP_PROJECT_ID)
            .with_string_input("region", self.region, _DOC_GCP_REGION)
        )

        if service_name:
            env = env.with_string_input("service_name", service_name, "The service to troubleshoot")

        env = env.with_string_output("result", "Diagnosis and recommended actions")

        work = await self._build_llm(env, "troubleshoot_prompt.md", source, task="troubleshoot")
        return await _get_result_or_last_reply(work)

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

        if source:
            self.source = source

        env = (
            dag.env()
            .with_string_input("service_name", service_name, "Service to upgrade")
            .with_string_input("project_id", self.project_id, _DOC_GCP_PROJECT_ID)
            .with_string_input("region", self.region, _DOC_GCP_REGION)
            .with_string_output("result", "Upgrade result")
        )

        if target_version:
            env = env.with_string_input("target_version", target_version, "Target version or image tag")
        if source:
            env = env.with_workspace(source)
        if dry_run:
            env = env.with_string_input("dry_run", "true", "Only analyze and report, do not apply changes")

        work = await self._build_llm(env, "upgrade_prompt.md", source, task="upgrade")
        return await _get_result_or_last_reply(work)

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
        # Store PR state for the suggestion tool
        self._github_token = github_token
        self._pr_repo = repo
        self._pr_number = pr_number
        self._pr_commit_sha = commit_sha

        # Truncate error output (keep tail — most relevant)
        max_error_chars = 8000
        if len(error_output) > max_error_chars:
            error_output = "...(truncated)\n" + error_output[-max_error_chars:]

        env = (
            dag.env()
            .with_string_input("error_output", error_output, "The CI error output to analyze")
            .with_string_input("pr_number", str(pr_number), "The pull request number")
            .with_string_input("repo", repo, "The GitHub repository URL")
            .with_string_input("commit_sha", commit_sha, "The HEAD commit SHA of the PR")
            .with_string_output("result", "Summary of suggestions posted")
        )

        if source:
            self.source = source
            env = env.with_workspace(source)

        # Skip _resolve_all — GCP auth not needed for suggesting code fixes
        work = await self._build_suggest_fix_llm(env, source)
        return await _get_result_or_last_reply(work)

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

        params, fallback = _parse_router_response(params_json)
        if fallback:
            function_name = fallback

        # Filter params to expected keys per function to prevent TypeErrors
        _allowed_keys = {
            "deploy": {"assignment", "service_name", "repository"},
            "troubleshoot": {"issue", "service_name"},
            "upgrade": {"service_name", "target_version"},
        }
        allowed = _allowed_keys.get(function_name, set())
        params = {k: v for k, v in params.items() if k in allowed}

        result = await self._execute_routed_function(
            function_name, params, body, workspace,
            gh, repository, issue_id, suggest_github_fix_on_failure,
        )

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

    async def _execute_routed_function(
        self,
        function_name: str,
        params: dict,
        body: str,
        workspace: dagger.Directory | None,
        gh,
        repository: str,
        issue_id: int,
        suggest_on_failure: bool,
    ) -> str:
        """Dispatch to the routed function, posting a comment on failure if requested."""
        try:
            if function_name == "deploy":
                return await self.deploy(source=workspace, **params)
            elif function_name == "troubleshoot":
                return await self.troubleshoot(source=workspace, **params)
            elif function_name == "upgrade":
                return await self.upgrade(source=workspace, **params)
            else:
                return await self.assist(assignment=body, source=workspace)
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
        )

        # Block entrypoints (prevent recursion) and destructive tools (read-only sub-agent)
        for fn in _BLOCKED_ENTRYPOINTS + ["task"] + _BLOCKED_DESTRUCTIVE:
            llm = llm.with_blocked_function("Goose", fn)

        llm = llm.with_prompt(f"## Task: {description}\n\n{prompt}")

        return await _get_result_or_last_reply(llm)

    # --- GitHub suggestion tool (exposed to LLM via with_current_module) ---

    @function
    async def suggest_github_pr_code_comment(
        self,
        path: Annotated[str, Doc("File path relative to repo root")],
        line: Annotated[int, Doc("Line number to suggest a change on")],
        suggestion: Annotated[str, Doc("Replacement code (no ```suggestion fences, just the raw code)")],
        comment: Annotated[str, Doc("Explanation of the fix")] = "",
    ) -> str:
        """Post an inline code suggestion on a GitHub pull request.

        The suggestion will appear as a GitHub "suggested change" that
        developers can apply with one click.
        """
        if not self._github_token or not self._pr_repo:
            raise ValueError("suggest_github_pr_code_comment can only be used during suggest_github_fix")

        body = ""
        if comment:
            body += f"{comment}\n\n"
        body += f"```suggestion\n{suggestion}\n```"

        gh = dag.github_issue(token=self._github_token)
        await gh.write_pull_request_code_comment(
            repo=self._pr_repo,
            issue_id=self._pr_number,
            commit=self._pr_commit_sha,
            body=body,
            path=path,
            side="RIGHT",
            line=line,
        )
        return f"Posted suggestion on {path}:{line}"

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
            raise ValueError(_ERROR_NO_SOURCE_DIR)
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
            raise ValueError(_ERROR_NO_SOURCE_DIR)
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
            raise ValueError(_ERROR_NO_SOURCE_DIR)
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
            raise ValueError(_ERROR_NO_SOURCE_DIR)
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
            raise ValueError(_ERROR_NO_SOURCE_DIR)
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
