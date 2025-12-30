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
        tag: Annotated[str, Doc("Image tag")] = "latest",
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        credentials: Annotated[dagger.Secret | None, Doc("GCP credentials")] = None,
    ) -> str:
        """Publish container to GCP Artifact Registry and return image URI."""
        hostname = f"{region}-docker.pkg.dev"
        image_uri = f"{hostname}/{project_id}/{repository}/{image_name}:{tag}"

        if credentials:
            gcp_auth = dag.gcp_auth()
            gcloud = gcp_auth.gcloud_container(
                credentials=credentials,
                project_id=project_id,
                region=region,
            )

            token_output = await (
                gcloud
                .with_exec(["gcloud", "auth", "print-access-token"])
                .stdout()
            )
            access_token = token_output.strip()
            token_secret = dag.set_secret("gcp_access_token", access_token)

            image_ref = await (
                container
                .with_registry_auth(
                    address=hostname,
                    username="oauth2accesstoken",
                    secret=token_secret,
                )
                .publish(image_uri)
            )
        else:
            image_ref = await container.publish(image_uri)

        return image_ref

    @function
    async def create_repository(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name to create")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        format: Annotated[str, Doc("Repository format: docker or generic")] = "docker",
        description: Annotated[str, Doc("Repository description")] = "",
    ) -> str:
        """Create an Artifact Registry repository (docker or generic format)."""
        gcp_auth = dag.gcp_auth()
        gcloud = gcp_auth.gcloud_container(
            credentials=credentials, project_id=project_id, region=region
        )

        if not description:
            description = "Docker container images" if format == "docker" else "Generic artifacts"

        output = await (
            gcloud
            .with_exec([
                "gcloud", "artifacts", "repositories", "create", repository,
                f"--repository-format={format}",
                f"--location={region}",
                f"--description={description}",
            ])
            .stdout()
        )

        return output

    @function
    async def list_images(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """List images in an Artifact Registry repository."""
        gcp_auth = dag.gcp_auth()
        gcloud = gcp_auth.gcloud_container(
            credentials=credentials, project_id=project_id, region=region
        )

        output = await (
            gcloud
            .with_exec([
                "gcloud", "artifacts", "docker", "images", "list",
                f"{region}-docker.pkg.dev/{project_id}/{repository}",
                "--format=table(IMAGE,TAGS,CREATE_TIME)",
            ])
            .stdout()
        )

        return output

    @function
    def get_image_uri(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Repository name")],
        image_name: Annotated[str, Doc("Image name")],
        tag: Annotated[str, Doc("Image tag")] = "latest",
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Construct full Artifact Registry image URI."""
        return f"{region}-docker.pkg.dev/{project_id}/{repository}/{image_name}:{tag}"

    @function
    async def upload_generic(
        self,
        directory: Annotated[dagger.Directory, Doc("Directory containing files to upload")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Generic Artifact Registry repository name")],
        package: Annotated[str, Doc("Package name")],
        version: Annotated[str, Doc("Package version")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        file_pattern: Annotated[str, Doc("Glob pattern for files to upload")] = "*",
    ) -> str:
        """Upload files to a generic Artifact Registry repository."""
        gcp_auth = dag.gcp_auth()
        gcloud = gcp_auth.gcloud_container(
            credentials=credentials, project_id=project_id, region=region
        )

        gcloud = (
            gcloud
            .with_mounted_directory("/upload", directory)
            .with_workdir("/upload")
        )

        upload_cmd = (
            f"for file in {file_pattern}; do "
            f"[ -f \"$file\" ] && "
            f"gcloud artifacts generic upload "
            f"--project={project_id} "
            f"--repository={repository} "
            f"--location={region} "
            f"--package={package} "
            f"--version={version} "
            f"--source=\"$file\" "
            f"--quiet 2>&1 || true; "
            f"done"
        )

        output = await (
            gcloud
            .with_exec(["sh", "-c", upload_cmd])
            .stdout()
        )

        return output

    @function
    def test_get_image_uri(self) -> str:
        """Test: Construct image URI (no credentials needed)."""
        uri = self.get_image_uri("test-project", "test-repo", "test-image", "v1.0.0")
        expected = "us-central1-docker.pkg.dev/test-project/test-repo/test-image:v1.0.0"
        if uri != expected:
            raise ValueError(f"Expected {expected}, got {uri}")
        return f"PASS: get_image_uri -> {uri}"

    @function
    async def test_all(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Existing repository name")],
    ) -> str:
        """Run all tests (requires GCP credentials)."""
        results = []
        results.append(self.test_get_image_uri())
        await self.list_images(project_id, repository, credentials)
        results.append(f"PASS: list_images -> {repository}")
        return "\n".join(results)

    @function
    async def test_all_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Existing repository name")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run all tests using GitHub Actions OIDC directly."""
        results = []
        results.append(self.test_get_image_uri())

        # Use gcloud_container_from_github_actions directly (bypasses oidc_credentials)
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        await (
            gcloud
            .with_exec([
                "gcloud", "artifacts", "docker", "images", "list",
                f"{region}-docker.pkg.dev/{project_id}/{repository}",
                "--format=table(IMAGE,TAGS,CREATE_TIME)",
            ])
            .stdout()
        )
        results.append(f"PASS: list_images -> {repository}")
        return "\n".join(results)
