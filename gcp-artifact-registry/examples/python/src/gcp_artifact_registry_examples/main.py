"""Examples for using the gcp-artifact-registry Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpArtifactRegistryExamples:
    """Usage examples for gcp-artifact-registry module."""

    @function
    async def publish_container(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with Dockerfile")],
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name")],
        image_name: Annotated[str, Doc("Image name")],
        tag: Annotated[str, Doc("Image tag")] = "latest",
    ) -> str:
        """Example: Build and publish a container to Artifact Registry."""
        container = source.docker_build()

        image_ref = await dag.gcp_artifact_registry().publish(
            container=container,
            project_id=project_id,
            repository=repository,
            image_name=image_name,
            tag=tag,
            gcloud=gcloud,
        )

        return f"Published: {image_ref}"

    @function
    async def publish_container_with_docker_config(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with Dockerfile")],
        docker_config: Annotated[dagger.File, Doc("Docker config.json file (e.g. $HOME/.docker/config.json)")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name")],
        image_name: Annotated[str, Doc("Image name")],
        tag: Annotated[str, Doc("Image tag")] = "latest",
    ) -> str:
        """Example: Build and publish using local Docker config credentials.

        Useful for local development when you already have Docker configured
        with `gcloud auth configure-docker`.

        Usage:
            dagger call publish-container-with-docker-config \
                --source=. \
                --docker-config=$HOME/.docker/config.json \
                --project-id=my-project \
                --repository=my-repo \
                --image-name=my-app
        """
        container = source.docker_build()

        image_ref = await dag.gcp_artifact_registry().publish(
            container=container,
            project_id=project_id,
            repository=repository,
            image_name=image_name,
            tag=tag,
            docker_config=docker_config,
        )

        return f"Published: {image_ref}"

    @function
    async def list_repository_images(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name")],
    ) -> str:
        """Example: List all images in an Artifact Registry repository."""
        return await dag.gcp_artifact_registry().list_images(
            gcloud=gcloud,
            project_id=project_id,
            repository=repository,
        )
