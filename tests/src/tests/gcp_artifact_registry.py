"""Tests for gcp-artifact-registry module."""

import dagger
from dagger import dag


async def test_gcp_artifact_registry(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    repository: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> str:
    """Run gcp-artifact-registry module tests using GitHub Actions OIDC."""
    results = []

    # Test get_image_uri (no credentials needed)
    ar = dag.gcp_artifact_registry()
    uri = await ar.get_image_uri(
        project_id="test-project",
        repository="test-repo",
        image_name="test-image",
        tag="v1.0.0",
    )
    expected = "us-central1-docker.pkg.dev/test-project/test-repo/test-image:v1.0.0"
    if uri != expected:
        raise ValueError(f"Expected {expected}, got {uri}")
    results.append(f"PASS: get_image_uri -> {uri}")

    # Get gcloud container from gcp-auth, then pass to artifact-registry
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )

    # Test list_images using the module function
    await ar.list_images(gcloud=gcloud, project_id=project_id, repository=repository, region=region)
    results.append(f"PASS: list_images -> {repository}")

    return "\n".join(results)
