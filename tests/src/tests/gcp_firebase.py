"""Tests for gcp-firebase module.

Tests all authentication methods:
- OIDC (recommended): Workload Identity Federation via GitHub Actions
- Service Account: Direct JSON key file
- Access Token (legacy): Pre-fetched bearer token

Each auth method is tested with:
- Firebase Hosting (build, deploy_preview, delete_channel)
- Firestore CRUD (create, read, update, delete)
- Scripts (node execution)
"""

import time

import dagger
from dagger import dag

from .auth_utils import (
    AuthMethod,
    format_auth_header,
    format_component_header,
    format_operation,
    format_test_summary,
    warn_legacy_access_token,
    get_access_token_from_service_account,
)
from ._gcp_firebase_helpers import (
    test_hosting_crud,
    test_firestore_crud,
    test_scripts,
)


# Fixtures path relative to module root
FIXTURES_PATH = "src/tests/fixtures/firestore-scripts"


async def test_gcp_firebase_oidc(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "europe-west9",
) -> tuple[str, dict[str, str]]:
    """Test gcp-firebase module with OIDC authentication (recommended).

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    results = [format_auth_header(AuthMethod.OIDC)]
    ops = {}

    # Get OIDC token with GCP audience
    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    firebase_oidc_token = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=audience,
    )

    # Get gcloud container for Firestore operations
    gcloud = dag.gcp_auth().gcloud_container_from_oidc_token(
        oidc_token=firebase_oidc_token,
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        service_account_email=service_account,
        region=region,
    )

    # Source directories
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()
    scripts_source = dag.current_module().source().directory(FIXTURES_PATH)

    # Test Hosting
    hosting_results, hosting_ops = await test_hosting_crud(
        project_id=project_id,
        source=source,
        auth_method=AuthMethod.OIDC,
        oidc_token=firebase_oidc_token,
        workload_identity_provider=workload_identity_provider,
        service_account_email=service_account,
    )
    results.extend(hosting_results)
    ops.update(hosting_ops)

    # Test Firestore
    firestore_results, firestore_ops = await test_firestore_crud(
        gcloud=gcloud,
        auth_method=AuthMethod.OIDC,
        region=region,
    )
    results.extend(firestore_results)
    ops.update(firestore_ops)

    # Test Scripts (create temp database for script test)
    database_id = f"script-test-{int(time.time())}"
    firestore = dag.gcp_firebase().firestore()
    try:
        await firestore.create(gcloud=gcloud, database_id=database_id, location=region)
        scripts_results, scripts_ops = await test_scripts(
            project_id=project_id,
            scripts_source=scripts_source,
            database_id=database_id,
            auth_method=AuthMethod.OIDC,
            oidc_token=firebase_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
        )
        results.extend(scripts_results)
        ops.update(scripts_ops)
    finally:
        try:
            await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
            await firestore.delete(gcloud=gcloud, database_id=database_id)
        except Exception:
            pass

    return "\n".join(results), ops


async def test_gcp_firebase_service_account(
    credentials: dagger.Secret,
    project_id: str,
    region: str = "europe-west9",
) -> tuple[str, dict[str, str]]:
    """Test gcp-firebase module with service account JSON key.

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    results = [format_auth_header(AuthMethod.SERVICE_ACCOUNT)]
    ops = {}

    # Get gcloud container for Firestore operations
    gcloud = dag.gcp_auth().gcloud_container(
        credentials=credentials,
        project_id=project_id,
        region=region,
    )

    # Source directories
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()
    scripts_source = dag.current_module().source().directory(FIXTURES_PATH)

    # Test Hosting
    hosting_results, hosting_ops = await test_hosting_crud(
        project_id=project_id,
        source=source,
        auth_method=AuthMethod.SERVICE_ACCOUNT,
        credentials=credentials,
    )
    results.extend(hosting_results)
    ops.update(hosting_ops)

    # Test Firestore
    firestore_results, firestore_ops = await test_firestore_crud(
        gcloud=gcloud,
        auth_method=AuthMethod.SERVICE_ACCOUNT,
        region=region,
    )
    results.extend(firestore_results)
    ops.update(firestore_ops)

    # Test Scripts (create temp database for script test)
    database_id = f"script-test-{int(time.time())}"
    firestore = dag.gcp_firebase().firestore()
    try:
        await firestore.create(gcloud=gcloud, database_id=database_id, location=region)
        scripts_results, scripts_ops = await test_scripts(
            project_id=project_id,
            scripts_source=scripts_source,
            database_id=database_id,
            auth_method=AuthMethod.SERVICE_ACCOUNT,
            credentials=credentials,
        )
        results.extend(scripts_results)
        ops.update(scripts_ops)
    finally:
        try:
            await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
            await firestore.delete(gcloud=gcloud, database_id=database_id)
        except Exception:
            pass

    return "\n".join(results), ops


async def test_gcp_firebase_access_token(
    project_id: str,
    credentials: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account: str | None = None,
    oidc_token: dagger.Secret | None = None,
    oidc_url: dagger.Secret | None = None,
    region: str = "europe-west9",
) -> tuple[str, dict[str, str]]:
    """Test gcp-firebase module with access token (LEGACY - NOT RECOMMENDED).

    If credentials (SA key) are provided, generates token from SA key.
    Otherwise, generates token from OIDC credentials.

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    warn_legacy_access_token()
    results = [format_auth_header(AuthMethod.ACCESS_TOKEN)]
    ops = {}

    # Generate access token from Service Account key (if provided)
    if credentials:
        results.append("  NOTE: access_token from Service Account Key")
        access_token = await get_access_token_from_service_account(
            credentials=credentials,
            project_id=project_id,
            region=region,
        )
    elif oidc_token and oidc_url and workload_identity_provider:
        results.append("  NOTE: access_token from OIDC")
        # Generate access token from OIDC (for testing legacy method)
        # Note: Cross-module calls returning Secret don't need await
        access_token = dag.gcp_auth().access_token_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
        )
    else:
        results.append(format_operation("ALL", "SKIP", "No credentials provided"))
        ops = {
            "H_BUILD": "SKIP", "H_DEPLOY": "SKIP", "H_DELETE": "SKIP",
            "F_CREATE": "SKIP", "F_READ": "SKIP", "F_UPDATE": "SKIP", "F_DELETE": "SKIP",
            "S_NODE": "SKIP", "S_CONTAINER": "SKIP",
        }
        return "\n".join(results), ops

    # Source directory
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()

    # Test Hosting only (access token not supported for scripts)
    hosting_results, hosting_ops = await test_hosting_crud(
        project_id=project_id,
        source=source,
        auth_method=AuthMethod.ACCESS_TOKEN,
        access_token=access_token,
    )
    results.extend(hosting_results)
    ops.update(hosting_ops)

    # Test Firestore (uses gcloud container, not access token directly)
    # Note: We test Firestore with gcloud from OIDC since access token flow
    # doesn't apply to gcloud CLI operations
    results.append(format_component_header("Firestore"))
    results.append(format_operation("ALL", "SKIP", "Firestore uses gcloud (tested via OIDC)"))
    ops["F_CREATE"] = "SKIP"
    ops["F_READ"] = "SKIP"
    ops["F_UPDATE"] = "SKIP"
    ops["F_DELETE"] = "SKIP"

    # Scripts don't support access token
    scripts_results, scripts_ops = await test_scripts(
        project_id=project_id,
        scripts_source=dag.current_module().source().directory(FIXTURES_PATH),
        database_id="dummy",  # Not used since access token is skipped
        auth_method=AuthMethod.ACCESS_TOKEN,
    )
    results.extend(scripts_results)
    ops.update(scripts_ops)

    return "\n".join(results), ops


async def test_gcp_firebase(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "europe-west9",
    credentials: dagger.Secret | None = None,
) -> str:
    """Run all gcp-firebase module tests with available auth methods.

    Args:
        workload_identity_provider: GCP WIF provider resource name
        service_account: Service account email
        project_id: GCP project ID
        oidc_token: ACTIONS_ID_TOKEN_REQUEST_TOKEN
        oidc_url: ACTIONS_ID_TOKEN_REQUEST_URL
        region: GCP region for Firestore
        credentials: Optional service account JSON key for SA tests
    """
    all_results = []
    summary_data = {}

    # Always test OIDC (available in GitHub Actions)
    oidc_result, oidc_ops = await test_gcp_firebase_oidc(
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
        sa_result, sa_ops = await test_gcp_firebase_service_account(
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
        summary_data["SERVICE_ACCOUNT"] = {
            "H_BUILD": "SKIP", "H_DEPLOY": "SKIP", "H_DELETE": "SKIP",
            "F_CREATE": "SKIP", "F_READ": "SKIP", "F_UPDATE": "SKIP", "F_DELETE": "SKIP",
            "S_NODE": "SKIP", "S_CONTAINER": "SKIP",
        }

    # Test access token (legacy)
    token_result, token_ops = await test_gcp_firebase_access_token(
        project_id=project_id,
        credentials=credentials,
        workload_identity_provider=workload_identity_provider,
        service_account=service_account,
        oidc_token=oidc_token,
        oidc_url=oidc_url,
        region=region,
    )
    all_results.append(token_result)
    summary_data["ACCESS_TOKEN"] = token_ops

    # Add summary table
    all_results.append(format_test_summary(summary_data))

    return "\n\n".join(all_results)
