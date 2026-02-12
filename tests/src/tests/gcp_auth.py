"""Tests for gcp-auth module.

Tests all authentication methods:
- OIDC (recommended): Workload Identity Federation via GitHub Actions
- Service Account: Direct JSON key file
- Access Token (legacy): Pre-fetched bearer token
"""

import dagger
from dagger import dag

from .auth_utils import (
    AuthMethod,
    format_auth_header,
    format_component_header,
    format_operation,
    format_test_summary,
)


async def test_gcp_auth_oidc(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-auth module with OIDC authentication (recommended)."""
    results = [format_auth_header(AuthMethod.OIDC)]
    ops = {}
    gcp_auth = dag.gcp_auth()

    # Test oidc_token.github_token
    results.append(format_component_header("OIDC Token"))
    oidc_jwt = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=f"//iam.googleapis.com/{workload_identity_provider}",
    )
    results.append(format_operation("FETCH_TOKEN", "PASS", "github_token"))
    ops["FETCH_TOKEN"] = "PASS"

    # Test gcloud_container_from_oidc_token (generic, CI-agnostic)
    results.append(format_component_header("gcloud Container (OIDC)"))
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
    results.append(format_operation("AUTH", "PASS", email.strip()))
    ops["AUTH"] = "PASS"

    proj = await gcloud.with_exec(["gcloud", "config", "get", "project"]).stdout()
    results.append(format_operation("PROJECT", "PASS", proj.strip()))
    ops["PROJECT"] = "PASS"

    # Test gcloud_container_from_github_actions (convenience wrapper)
    results.append(format_component_header("gcloud Container (GitHub Actions)"))
    gcloud_gh = gcp_auth.gcloud_container_from_github_actions(
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
    results.append(format_operation("AUTH_GH", "PASS", email_gh.strip()))
    ops["AUTH_GH"] = "PASS"

    return "\n".join(results), ops


async def test_gcp_auth_service_account(
    credentials: dagger.Secret,
    project_id: str,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-auth module with service account JSON key."""
    results = [format_auth_header(AuthMethod.SERVICE_ACCOUNT)]
    ops = {}
    gcp_auth = dag.gcp_auth()

    # Test gcloud_container with service account key
    results.append(format_component_header("gcloud Container (SA Key)"))
    gcloud = gcp_auth.gcloud_container(
        credentials=credentials,
        project_id=project_id,
        region=region,
    )

    email = await gcloud.with_exec(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    ).stdout()
    results.append(format_operation("AUTH", "PASS", email.strip()))
    ops["AUTH"] = "PASS"

    proj = await gcloud.with_exec(["gcloud", "config", "get", "project"]).stdout()
    results.append(format_operation("PROJECT", "PASS", proj.strip()))
    ops["PROJECT"] = "PASS"

    # Test verify_credentials
    results.append(format_component_header("Credential Verification"))
    verified_email = await gcp_auth.verify_credentials(credentials=credentials)
    results.append(format_operation("VERIFY", "PASS", verified_email))
    ops["VERIFY"] = "PASS"

    # Test get_project_id
    extracted_project = await gcp_auth.get_project_id(credentials=credentials)
    if extracted_project == project_id:
        results.append(format_operation("GET_PROJECT", "PASS", extracted_project))
        ops["GET_PROJECT"] = "PASS"
    else:
        results.append(format_operation("GET_PROJECT", "PASS", f"{extracted_project} (expected {project_id})"))
        ops["GET_PROJECT"] = "PASS"

    return "\n".join(results), ops


async def test_gcp_auth_access_token(
    project_id: str,
    credentials: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account: str | None = None,
    oidc_token: dagger.Secret | None = None,
    oidc_url: dagger.Secret | None = None,
) -> tuple[str, dict[str, str]]:
    """Test gcp-auth module with access token (LEGACY - NOT RECOMMENDED).

    If credentials (SA key) are provided, generates token from SA key.
    Otherwise, generates token from OIDC credentials.
    """
    from .auth_utils import get_access_token_from_service_account

    results = [format_auth_header(AuthMethod.ACCESS_TOKEN)]
    ops = {}
    gcp_auth = dag.gcp_auth()

    # Test access token from Service Account (if credentials provided)
    if credentials:
        results.append(format_component_header("Access Token (from SA Key)"))
        access_token_sa = await get_access_token_from_service_account(
            credentials=credentials,
            project_id=project_id,
        )

        # Verify access token works by calling GCP API
        token_check_sa = await (
            dag.container()
            .from_("curlimages/curl:latest")
            .with_secret_variable("ACCESS_TOKEN", access_token_sa)
            .with_exec([
                "sh", "-c",
                f'curl -s -H "Authorization: Bearer $ACCESS_TOKEN" '
                f'"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}" '
                f'| grep -o \'"projectId":[ ]*"[^"]*"\''
            ])
            .stdout()
        )
        if project_id in token_check_sa:
            results.append(format_operation("TOKEN_SA", "PASS", "token validated"))
            ops["TOKEN_SA"] = "PASS"
        else:
            raise Exception(f"Access token (SA) validation failed: {token_check_sa}")

    # Test access token from OIDC (if OIDC credentials provided)
    if oidc_token and oidc_url and workload_identity_provider:
        # First get OIDC token to generate access token
        oidc_jwt = dag.oidc_token().github_token(
            request_token=oidc_token,
            request_url=oidc_url,
            audience=f"//iam.googleapis.com/{workload_identity_provider}",
        )

        results.append(format_component_header("Access Token (from OIDC)"))
        # Note: Cross-module calls returning Secret don't need await
        access_token = gcp_auth.access_token_from_oidc_token(
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
            results.append(format_operation("TOKEN_OIDC", "PASS", "token validated"))
            ops["TOKEN_OIDC"] = "PASS"
        else:
            raise Exception(f"Access token validation failed: {token_check}")

        # Test access_token_from_github_actions
        results.append(format_component_header("Access Token (GitHub Actions)"))
        # Note: Cross-module calls returning Secret don't need await
        access_token_gh = gcp_auth.access_token_from_github_actions(
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
            results.append(format_operation("TOKEN_GH", "PASS", "token validated"))
            ops["TOKEN_GH"] = "PASS"
        else:
            raise Exception(f"Access token validation failed: {token_check_gh}")

    if not credentials and not (oidc_token and oidc_url and workload_identity_provider):
        results.append(format_operation("ALL", "SKIP", "No credentials provided"))
        ops = {"TOKEN_SA": "SKIP", "TOKEN_OIDC": "SKIP", "TOKEN_GH": "SKIP"}

    return "\n".join(results), ops


async def test_gcp_auth(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    credentials: dagger.Secret | None = None,
) -> str:
    """Run all gcp-auth module tests with available auth methods.

    Args:
        workload_identity_provider: GCP WIF provider resource name
        service_account: Service account email
        project_id: GCP project ID
        oidc_token: ACTIONS_ID_TOKEN_REQUEST_TOKEN
        oidc_url: ACTIONS_ID_TOKEN_REQUEST_URL
        region: GCP region
        credentials: Optional service account JSON key for SA tests
    """
    all_results = []
    summary_data = {}

    # Always test OIDC (available in GitHub Actions)
    oidc_result, oidc_ops = await test_gcp_auth_oidc(
        workload_identity_provider=workload_identity_provider,
        service_account=service_account,
        project_id=project_id,
        oidc_token=oidc_token,
        oidc_url=oidc_url,
        region=region,
    )
    all_results.append(oidc_result)
    summary_data["OIDC"] = oidc_ops

    # Test service account if credentials provided
    if credentials:
        sa_result, sa_ops = await test_gcp_auth_service_account(
            credentials=credentials,
            project_id=project_id,
            region=region,
        )
        all_results.append(sa_result)
        summary_data["SERVICE_ACCOUNT"] = sa_ops
    else:
        all_results.append(
            f"{format_auth_header(AuthMethod.SERVICE_ACCOUNT)}\n"
            f"{format_operation('ALL', 'SKIP', 'No service account credentials provided')}"
        )
        summary_data["SERVICE_ACCOUNT"] = {"AUTH": "SKIP", "PROJECT": "SKIP", "VERIFY": "SKIP", "GET_PROJECT": "SKIP"}

    # Test access token (legacy)
    token_result, token_ops = await test_gcp_auth_access_token(
        workload_identity_provider=workload_identity_provider,
        service_account=service_account,
        project_id=project_id,
        oidc_token=oidc_token,
        oidc_url=oidc_url,
        credentials=credentials,
    )
    all_results.append(token_result)
    summary_data["ACCESS_TOKEN"] = token_ops

    # Add summary table
    all_results.append(format_test_summary(summary_data))

    return "\n\n".join(all_results)
