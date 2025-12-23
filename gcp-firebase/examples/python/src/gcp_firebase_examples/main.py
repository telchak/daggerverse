"""Examples for using the gcp-firebase Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpFirebaseExamples:
    """Usage examples for gcp-firebase module."""

    @function
    async def deploy_to_production(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("Firebase project ID")],
    ) -> str:
        """Example: Build and deploy web app to Firebase Hosting."""
        result = await dag.gcp_firebase().deploy(
            credentials=credentials,
            project_id=project_id,
            source=source,
            build_command="npm run build",
            deploy_functions=True,
        )

        return f"Deployed to production: {result}"

    @function
    async def deploy_preview_for_pr(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        pr_number: Annotated[int, Doc("Pull request number")],
    ) -> str:
        """Example: Deploy a preview channel for a pull request."""
        preview_url = await dag.gcp_firebase().deploy_preview(
            credentials=credentials,
            project_id=project_id,
            channel_id=f"pr-{pr_number}",
            source=source,
            build_command="npm run build",
            expires="7d",
        )

        return f"Preview available at: {preview_url}"
