"""GCP Artifact Registry Module - Operations for Google Cloud Artifact Registry."""

import re
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


# Validation patterns for GCP resource names
_GCP_PROJECT_ID_PATTERN = re.compile(r'^[a-z][a-z0-9-]{5,29}$')
_GCP_REGION_PATTERN = re.compile(r'^[a-z]+-[a-z]+\d+(-[a-z])?$')
_REPOSITORY_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9-]{0,62}$')
_PACKAGE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$')
_VERSION_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._+-]{0,127}$')
_SAFE_GLOB_PATTERN = re.compile(r'^[a-zA-Z0-9.*_-]+$')


def _validate_project_id(project_id: str) -> str:
    """Validate GCP project ID format."""
    if not _GCP_PROJECT_ID_PATTERN.match(project_id):
        raise ValueError(f"Invalid GCP project ID: '{project_id}'")
    return project_id


def _validate_region(region: str) -> str:
    """Validate GCP region format."""
    if not _GCP_REGION_PATTERN.match(region):
        raise ValueError(f"Invalid GCP region format: '{region}'")
    return region


def _validate_repository(repository: str) -> str:
    """Validate Artifact Registry repository name."""
    if not _REPOSITORY_NAME_PATTERN.match(repository):
        raise ValueError(f"Invalid repository name: '{repository}'")
    return repository


def _validate_package(package: str) -> str:
    """Validate package name."""
    if not _PACKAGE_NAME_PATTERN.match(package):
        raise ValueError(f"Invalid package name: '{package}'")
    return package


def _validate_version(version: str) -> str:
    """Validate version string."""
    if not _VERSION_PATTERN.match(version):
        raise ValueError(f"Invalid version: '{version}'")
    return version


def _validate_glob_pattern(pattern: str) -> str:
    """Validate file glob pattern to prevent injection."""
    if not _SAFE_GLOB_PATTERN.match(pattern):
        raise ValueError(f"Invalid file pattern: '{pattern}'. Only alphanumeric, *, ., _, - allowed.")
    return pattern


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
        docker_config: Annotated[dagger.File | None, Doc("Docker config.json file with registry credentials (e.g. from ~/.docker/config.json)")] = None,
    ) -> str:
        """Publish container to GCP Artifact Registry and return image URI."""
        hostname = f"{region}-docker.pkg.dev"
        image_uri = f"{hostname}/{project_id}/{repository}/{image_name}:{tag}"

        if docker_config:
            return await (
                container
                .with_mounted_file("/root/.docker/config.json", docker_config)
                .publish(image_uri)
            )

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
        # Validate all inputs to prevent command injection
        _validate_project_id(project_id)
        _validate_repository(repository)
        _validate_package(package)
        _validate_version(version)
        _validate_region(region)
        _validate_glob_pattern(file_pattern)

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
