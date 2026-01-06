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

    # ========== OIDC TOKEN MODULE TEST ==========
    results.append("--- oidc_token.github_token ---")

    # Fetch OIDC token using oidc-token module
    oidc_jwt = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=f"//iam.googleapis.com/{workload_identity_provider}",
    )
    results.append("PASS: oidc_token.github_token -> token fetched")

    # ========== GENERIC OIDC FUNCTIONS TEST ==========
    results.append("--- gcloud_container_from_oidc_token ---")

    # Test generic OIDC function (CI-agnostic)
    gcloud = gcp_auth.gcloud_container_from_oidc_token(
        oidc_token=oidc_jwt,
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        service_account_email=service_account,
        region=region,
    )

    email = await gcloud.with_exec(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    ).stdout()
    results.append(f"PASS: gcloud auth -> {email.strip()}")

    proj = await gcloud.with_exec(["gcloud", "config", "get", "project"]).stdout()
    results.append(f"PASS: gcloud project -> {proj.strip()}")

    # ========== GITHUB ACTIONS CONVENIENCE WRAPPER TEST ==========
    results.append("--- gcloud_container_from_github_actions ---")

    # Test GitHub Actions convenience wrapper
    gcloud_gh = await gcp_auth.gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )

    email_gh = await gcloud_gh.with_exec(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    ).stdout()
    results.append(f"PASS: gcloud_container_from_github_actions -> {email_gh.strip()}")

    # ========== CREDENTIALS FROM OIDC TOKEN TEST ==========
    results.append("--- credentials_from_oidc_token ---")

    credentials = await gcp_auth.credentials_from_oidc_token(
        oidc_token=oidc_jwt,
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
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
    results.append(f"PASS: credentials_from_oidc_token -> {creds_email.strip()}")

    # ========== CREDENTIALS FROM GITHUB ACTIONS TEST ==========
    results.append("--- credentials_from_github_actions ---")

    credentials_gh = await gcp_auth.credentials_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
    )

    gcloud_from_creds_gh = gcp_auth.gcloud_container(
        credentials=credentials_gh,
        project_id=project_id,
        region=region,
    )
    creds_email_gh = await gcloud_from_creds_gh.with_exec(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    ).stdout()
    results.append(f"PASS: credentials_from_github_actions -> {creds_email_gh.strip()}")

    # ========== ACCESS TOKEN FROM OIDC TOKEN TEST ==========
    results.append("--- access_token_from_oidc_token ---")

    access_token = await gcp_auth.access_token_from_oidc_token(
        oidc_token=oidc_jwt,
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
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
            f'| grep -o \'"projectId":[ ]*"[^"]*"\''
        ])
        .stdout()
    )
    if project_id in token_check:
        results.append("PASS: access_token_from_oidc_token -> token works")
    else:
        raise Exception(f"Access token validation failed: {token_check}")

    # ========== ACCESS TOKEN FROM GITHUB ACTIONS TEST ==========
    results.append("--- access_token_from_github_actions ---")

    access_token_gh = await gcp_auth.access_token_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
    )

    token_check_gh = await (
        dag.container()
        .from_("curlimages/curl:latest")
        .with_secret_variable("ACCESS_TOKEN", access_token_gh)
        .with_exec([
            "sh", "-c",
            f'curl -s -H "Authorization: Bearer $ACCESS_TOKEN" '
            f'"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}" '
            f'| grep -o \'"projectId":[ ]*"[^"]*"\''
        ])
        .stdout()
    )
    if project_id in token_check_gh:
        results.append("PASS: access_token_from_github_actions -> token works")
    else:
        raise Exception(f"Access token validation failed: {token_check_gh}")

    return "\n".join(results)
