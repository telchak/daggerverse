"""GCP Artifact Registry Module - Operations for Google Cloud Artifact Registry."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpArtifactRegistry:
    """Google Cloud Artifact Registry utilities."""

    @function
    async def publish(
        self,
        container: Annotated[dagger.Container, Doc("Container to publish")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Artifact Registry repository name")],
        image_name: Annotated[str, Doc("Image name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        tag: Annotated[str, Doc("Image tag")] = "latest",
        gcloud: Annotated[dagger.Container | None, Doc("Authenticated gcloud container")] = None,
    ) -> str:
        """Publish container to GCP Artifact Registry and return image URI."""
        hostname = f"{region}-docker.pkg.dev"
        image_uri = f"{hostname}/{project_id}/{repository}/{image_name}:{tag}"

        if gcloud:
            token = await gcloud.with_exec(["gcloud", "auth", "print-access-token"]).stdout()
            token_secret = dag.set_secret("gcp_access_token", token.strip())
            return await (
                container
                .with_registry_auth(hostname, "oauth2accesstoken", token_secret)
                .publish(image_uri)
            )

        return await container.publish(image_uri)

    @function
    async def create_repository(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        repository: Annotated[str, Doc("Repository name to create")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        format: Annotated[str, Doc("Repository format: docker or generic")] = "docker",
        description: Annotated[str, Doc("Repository description")] = "",
    ) -> str:
        """Create an Artifact Registry repository."""
        if not description:
            description = "Docker container images" if format == "docker" else "Generic artifacts"

        return await (
            gcloud
            .with_exec([
                "gcloud", "artifacts", "repositories", "create", repository,
                f"--repository-format={format}",
                f"--location={region}",
                f"--description={description}",
            ])
            .stdout()
        )

    @function
    async def list_images(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """List images in an Artifact Registry repository."""
        return await (
            gcloud
            .with_exec([
                "gcloud", "artifacts", "docker", "images", "list",
                f"{region}-docker.pkg.dev/{project_id}/{repository}",
                "--format=table(IMAGE,TAGS,CREATE_TIME)",
            ])
            .stdout()
        )

    @function
    def get_image_uri(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name")],
        image_name: Annotated[str, Doc("Image name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        tag: Annotated[str, Doc("Image tag")] = "latest",
    ) -> str:
        """Construct full Artifact Registry image URI."""
        return f"{region}-docker.pkg.dev/{project_id}/{repository}/{image_name}:{tag}"

    @function
    async def upload_generic(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        directory: Annotated[dagger.Directory, Doc("Directory containing files to upload")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Generic repository name")],
        package: Annotated[str, Doc("Package name")],
        version: Annotated[str, Doc("Package version")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        file_pattern: Annotated[str, Doc("Glob pattern for files")] = "*",
    ) -> str:
        """Upload files to a generic Artifact Registry repository."""
        upload_cmd = (
            f"for file in {file_pattern}; do "
            f"[ -f \"$file\" ] && gcloud artifacts generic upload "
            f"--project={project_id} --repository={repository} --location={region} "
            f"--package={package} --version={version} --source=\"$file\" --quiet 2>&1 || true; done"
        )

        return await (
            gcloud
            .with_mounted_directory("/upload", directory)
            .with_workdir("/upload")
            .with_exec(["sh", "-c", upload_cmd])
            .stdout()
        )
