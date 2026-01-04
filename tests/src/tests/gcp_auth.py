"""Tests for gcp-auth module."""

import dagger
from dagger import dag


async def test_gcp_auth(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> str:
    """Run gcp-auth module tests using GitHub Actions OIDC."""
    results = []

    # Get authenticated gcloud container
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )

    # Test auth list
    email = await gcloud.with_exec(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    ).stdout()
    results.append(f"PASS: gcloud auth -> {email.strip()}")

    # Test project config
    proj = await gcloud.with_exec(["gcloud", "config", "get", "project"]).stdout()
    results.append(f"PASS: gcloud project -> {proj.strip()}")

    # Test projects describe
    desc = await gcloud.with_exec(
        ["gcloud", "projects", "describe", project_id, "--format=value(projectId)"]
    ).stdout()
    results.append(f"PASS: gcloud projects describe -> {desc.strip()}")

    return "\n".join(results)
