"""Examples for using the gcp-auth Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpAuthExamples:
    """Usage examples for gcp-auth module."""

    @function
    async def verify_service_account(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
    ) -> str:
        """Example: Verify service account credentials and get email."""
        email = await dag.gcp_auth().verify_credentials(credentials)
        return f"✓ Authenticated as: {email}"

    @function
    async def list_gcp_projects(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Example: List GCP projects using authenticated gcloud container."""
        gcloud = dag.gcp_auth().gcloud_container(
            credentials=credentials,
            project_id=project_id,
        )

        output = await gcloud.with_exec([
            "gcloud", "projects", "list", "--limit=5"
        ]).stdout()

        return output

    @function
    async def use_adc_locally(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Example: Use Application Default Credentials from host (local dev)."""
        gcloud = dag.gcp_auth().gcloud_container_from_host(
            project_id=project_id,
        )

        output = await gcloud.with_exec([
            "gcloud", "config", "get", "account"
        ]).stdout()

        return f"Using ADC account: {output.strip()}"

    @function
    async def get_project_from_credentials(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
    ) -> str:
        """Example: Extract project ID from service account credentials."""
        project_id = await dag.gcp_auth().get_project_id(credentials)
        return f"Project ID: {project_id}"

    @function
    def add_credentials_to_container(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
    ) -> dagger.Container:
        """Example: Add GCP credentials to custom container."""
        container = dag.container().from_("python:3.11-slim")

        authenticated = dag.gcp_auth().with_credentials(
            container=container,
            credentials=credentials,
        )

        return authenticated

    @function
    async def install_gcloud_components(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Example: Create gcloud container with additional components."""
        gcloud = dag.gcp_auth().gcloud_container(
            credentials=credentials,
            project_id=project_id,
            components=["kubectl", "gke-gcloud-auth-plugin"],
        )

        output = await gcloud.with_exec([
            "gcloud", "components", "list", "--only-local-state"
        ]).stdout()

        return output
