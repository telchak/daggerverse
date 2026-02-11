"""Examples for using the goose Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GooseExamples:
    """Usage examples for goose module."""

    @function
    async def deploy_cloud_run_service(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_name: Annotated[str, Doc("Service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: Deploy a public hello-world service to Cloud Run."""
        return await (
            dag.goose(
                gcloud=gcloud,
                project_id=project_id,
                region=region,
            )
            .deploy(
                assignment="Deploy gcr.io/google-samples/hello-app:1.0 as a public service with allow unauthenticated access",
                service_name=service_name,
            )
        )

    @function
    async def deploy_firebase_hosting(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        credentials: Annotated[dagger.Secret, Doc("Service account JSON key")],
        project_id: Annotated[str, Doc("GCP project ID")],
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: Deploy a web app to Firebase Hosting."""
        return await (
            dag.goose(
                gcloud=gcloud,
                project_id=project_id,
                region=region,
                credentials=credentials,
            )
            .deploy(
                assignment="Deploy to Firebase Hosting",
                service_name="firebase-site",
                source=source,
            )
        )

    @function
    async def troubleshoot_service(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        service_name: Annotated[str, Doc("Service name to troubleshoot")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: Troubleshoot a Cloud Run service returning errors."""
        return await (
            dag.goose(
                gcloud=gcloud,
                project_id=project_id,
                region=region,
            )
            .troubleshoot(
                service_name=service_name,
                issue="Service is returning 503 errors and seems to be crashing on startup",
            )
        )

    @function
    async def assist_list_services(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: List all Cloud Run services and report their status."""
        return await (
            dag.goose(
                gcloud=gcloud,
                project_id=project_id,
                region=region,
            )
            .assist(
                assignment="List all Cloud Run services and report their status",
            )
        )

    @function
    async def review_configs(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        source: Annotated[dagger.Directory, Doc("Source directory with deployment configs")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: Review deployment configs for best practices."""
        return await (
            dag.goose(
                gcloud=gcloud,
                project_id=project_id,
                region=region,
            )
            .review(
                source=source,
                focus="security and performance",
            )
        )

    @function
    async def upgrade_service(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_name: Annotated[str, Doc("Service to upgrade")],
        target_version: Annotated[str, Doc("New image tag")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: Upgrade a Cloud Run service to a new image version (dry run)."""
        return await (
            dag.goose(
                gcloud=gcloud,
                project_id=project_id,
                region=region,
            )
            .upgrade(
                service_name=service_name,
                target_version=target_version,
                dry_run=True,
            )
        )
