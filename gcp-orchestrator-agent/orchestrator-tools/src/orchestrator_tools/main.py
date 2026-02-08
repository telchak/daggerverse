"""Orchestrator tools — multi-service GCP tools for the orchestrator agent."""

from typing import Annotated

import dagger
from dagger import Doc, dag, field, function, object_type


@object_type
class OrchestratorTools:
    """Tools for Cloud Run, Artifact Registry, Firebase, Vertex AI, and health checks."""

    gcloud: Annotated[dagger.Container | None, Doc("Authenticated gcloud container")] = field(default=None)
    project_id: Annotated[str, Doc("GCP project ID")] = field(default="")
    region: Annotated[str, Doc("GCP region")] = field(default="")
    credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key for Firebase")] = field(default=None)
    firebase_oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token for Firebase (from CI provider)")] = field(
        default=None
    )
    firebase_workload_identity_provider: Annotated[
        str, Doc("GCP Workload Identity Federation provider for Firebase")
    ] = field(default="")
    firebase_service_account_email: Annotated[
        str, Doc("Service account to impersonate for Firebase")
    ] = field(default="")
    developer_knowledge_api_key: Annotated[
        dagger.Secret | None, Doc("Google Developer Knowledge API key (enables GCP docs search)")
    ] = field(default=None)

    # ========== Cloud Run ==========

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

    # ========== Artifact Registry ==========

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

    # ========== Firebase Hosting ==========

    def _firebase_auth_kwargs(self) -> dict:
        """Build authentication kwargs for gcp-firebase calls.

        Priority: 1) OIDC/WIF  2) Service account credentials  3) Error
        """
        if self.firebase_oidc_token and self.firebase_workload_identity_provider:
            kwargs: dict = {
                "oidc_token": self.firebase_oidc_token,
                "workload_identity_provider": self.firebase_workload_identity_provider,
            }
            if self.firebase_service_account_email:
                kwargs["service_account_email"] = self.firebase_service_account_email
            return kwargs
        if self.credentials:
            return {"credentials": self.credentials}
        raise ValueError(
            "Firebase operations require authentication. Provide either:\n"
            "  - firebase_oidc_token + firebase_workload_identity_provider (recommended for CI/CD)\n"
            "  - credentials (service account JSON key)"
        )

    @function
    async def deploy_firebase_hosting(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
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
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
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

    # ========== Vertex AI ==========

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
        """List all models in Vertex AI."""
        return await (
            dag.gcp_vertex_ai()
            .list_models(
                gcloud=self.gcloud,
                region=self.region,
            )
        )

    @function
    async def list_vertex_endpoints(self) -> str:
        """List all endpoints in Vertex AI."""
        return await (
            dag.gcp_vertex_ai()
            .list_endpoints(
                gcloud=self.gcloud,
                region=self.region,
            )
        )

    # ========== Health Check ==========

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

    # ========== Google Developer Knowledge (GCP Docs Search) ==========

    _DK_API_BASE = "https://developerknowledge.googleapis.com/v1alpha"

    def _require_dk_api_key(self) -> dagger.Secret:
        """Validate that the Developer Knowledge API key is available."""
        if self.developer_knowledge_api_key is None:
            raise ValueError(
                "GCP docs search requires 'developer_knowledge_api_key'. "
                "Pass the API key when constructing the orchestrator agent."
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
        document_name: Annotated[str, Doc("Document resource name from search results (the 'parent' field, e.g. 'documents/cloud.google.com/run/docs/...')")],
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
