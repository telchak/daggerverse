"""Tests for gcp-vertex-ai module."""

import dagger
from dagger import dag


async def test_gcp_vertex_ai(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> str:
    """Run gcp-vertex-ai module tests using GitHub Actions OIDC."""
    results = []

    # Get gcloud container from gcp-auth
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )

    vai = dag.gcp_vertex_ai()

    # Test list models
    await vai.list_models(gcloud=gcloud, region=region)
    results.append("PASS: list_models")

    # Test list endpoints
    await vai.list_endpoints(gcloud=gcloud, region=region)
    results.append("PASS: list_endpoints")

    return "\n".join(results)
