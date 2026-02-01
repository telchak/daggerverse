"""Cloud Run tools - provides LLM-callable tools for Cloud Run operations."""

from typing import Annotated

import dagger
from dagger import Doc, dag, field, function, object_type


@object_type
class CloudRunTools:
    """Tools for Cloud Run deployment and Artifact Registry operations."""

    gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")] = field()
    project_id: Annotated[str, Doc("GCP project ID")] = field()
    region: Annotated[str, Doc("GCP region")] = field()

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
