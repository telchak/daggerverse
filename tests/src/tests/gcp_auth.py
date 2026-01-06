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
    gcp_auth = dag.gcp_auth()

    # ========== GCLOUD CONTAINER TEST ==========
    results.append("--- gcloud_container_from_github_actions ---")

    gcloud = gcp_auth.gcloud_container_from_github_actions(
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

    # ========== CREDENTIALS FROM GITHUB ACTIONS TEST ==========
    results.append("--- credentials_from_github_actions ---")

    credentials = await gcp_auth.credentials_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
    )

    # Verify credentials work by using them with gcloud_container
    gcloud_from_creds = gcp_auth.gcloud_container(
        credentials=credentials,
        project_id=project_id,
        region=region,
    )
    creds_email = await gcloud_from_creds.with_exec(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    ).stdout()
    results.append(f"PASS: credentials_from_github_actions -> {creds_email.strip()}")

    # ========== ACCESS TOKEN FROM GITHUB ACTIONS TEST ==========
    results.append("--- access_token_from_github_actions ---")

    access_token = await gcp_auth.access_token_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
    )

    # Verify access token works by calling GCP API
    token_check = await (
        dag.container()
        .from_("curlimages/curl:latest")
        .with_secret_variable("ACCESS_TOKEN", access_token)
        .with_exec([
            "sh", "-c",
            f'curl -s -H "Authorization: Bearer $ACCESS_TOKEN" '
            f'"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}" '
            f'| grep -o \'"projectId":\s*"[^"]*"\''
        ])
        .stdout()
    )
    if project_id in token_check:
        results.append(f"PASS: access_token_from_github_actions -> token works")
    else:
        raise Exception(f"Access token validation failed: {token_check}")

    return "\n".join(results)
