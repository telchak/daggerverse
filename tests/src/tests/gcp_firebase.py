"""Tests for gcp-firebase module.

Tests the three authentication approaches:
- OIDC Token + Workload Identity Federation (for Hosting and Scripts)
- gcloud container (for Firestore operations that require gcloud CLI)
"""

import time

import dagger
from dagger import dag


# Fixtures path relative to module root
FIXTURES_PATH = "src/tests/fixtures/firestore-scripts"


async def test_gcp_firebase(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "europe-west9",
) -> str:
    """Run gcp-firebase module tests (Hosting + Firestore + Scripts).

    Uses OIDC token + WIF for Firebase Hosting and Scripts.
    Uses gcloud container (via gcp-auth) for Firestore operations.
    """
    results = []
    channel_id = f"dagger-test-{int(time.time())}"
    database_id = f"dagger-test-{int(time.time())}"

    # Get OIDC token from GitHub Actions with GCP audience
    # This is the recommended authentication method for Firebase operations
    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    firebase_oidc_token = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=audience,
    )

    # Get gcloud container from gcp-auth (needed for Firestore operations)
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
    )

    # Clone firebase-dagger-template from GitHub
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()

    # Load test fixtures for scripts tests (relative to module source)
    scripts_source = dag.current_module().source().directory(FIXTURES_PATH)

    firebase = dag.gcp_firebase()

    # ========== HOSTING TESTS (using OIDC token) ==========
    results.append("--- Firebase Hosting (OIDC auth) ---")

    # Test build (no auth required)
    dist = firebase.build(source=source)
    entries = await dist.entries()
    if len(entries) == 0:
        raise ValueError("Build produced no output files")
    results.append(f"PASS: build -> {len(entries)} files")

    try:
        # Test deploy_preview with OIDC token
        preview_url = await firebase.deploy_preview(
            project_id=project_id,
            channel_id=channel_id,
            source=source,
            oidc_token=firebase_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
        )
        if not preview_url.startswith("https://"):
            raise ValueError(f"Invalid preview URL: {preview_url}")
        results.append(f"PASS: deploy_preview (OIDC) -> {preview_url}")

        # Test delete_channel with OIDC token
        await firebase.delete_channel(
            project_id=project_id,
            channel_id=channel_id,
            oidc_token=firebase_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
        )
        results.append("PASS: delete_channel (OIDC)")

    except Exception as e:
        results.append(f"FAIL: {e}")
        try:
            await firebase.delete_channel(
                project_id=project_id,
                channel_id=channel_id,
                oidc_token=firebase_oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account,
            )
            results.append(f"CLEANUP: deleted channel {channel_id}")
        except Exception:
            pass
        raise

    # ========== FIRESTORE TESTS (using gcloud container) ==========
    results.append("--- Firestore (gcloud auth) ---")

    firestore = firebase.firestore()

    try:
        # CREATE
        await firestore.create(gcloud=gcloud, database_id=database_id, location=region)
        results.append(f"PASS: CREATE - created database {database_id}")

        # READ - exists
        exists = await firestore.exists(gcloud=gcloud, database_id=database_id)
        if not exists:
            raise Exception(f"Database {database_id} not found after create")
        results.append("PASS: READ - database exists")

        # READ - describe
        description = await firestore.describe(gcloud=gcloud, database_id=database_id)
        if database_id not in description:
            raise Exception(f"Database {database_id} not in describe output")
        results.append("PASS: READ - describe database")

        # READ - list
        db_list = await firestore.list_(gcloud=gcloud)
        if database_id not in db_list:
            raise Exception(f"Database {database_id} not in list output")
        results.append("PASS: READ - list databases")

        # UPDATE - enable then disable delete protection
        await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=True)
        results.append("PASS: UPDATE - enabled delete protection")

        await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
        results.append("PASS: UPDATE - disabled delete protection")

        # ========== SCRIPTS TESTS (using OIDC token) ==========
        results.append("--- Scripts (OIDC auth) ---")

        scripts = firebase.scripts()

        # Test scripts().node() - TypeScript script with OIDC token
        node_output = await scripts.node(
            source=scripts_source,
            script="seed-data.ts",
            oidc_token=firebase_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
            project_id=project_id,
            working_dir=".",
            install_command="npm install",  # No package-lock.json in fixtures
            env=[f"FIRESTORE_DATABASE_ID={database_id}"],
        )
        if '"status":"success"' not in node_output:
            raise Exception(f"Node script failed: {node_output}")
        results.append("PASS: scripts().node() - TypeScript seed script executed (OIDC)")

        # Test scripts().container() - verify OIDC credentials are configured
        container = scripts.container(
            source=scripts_source,
            base_image="alpine:latest",
            oidc_token=firebase_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
            project_id=project_id,
        )

        # Verify GOOGLE_APPLICATION_CREDENTIALS env var is set
        gac_check = await container.with_exec(["sh", "-c", "echo $GOOGLE_APPLICATION_CREDENTIALS"]).stdout()
        if "/tmp/gcp-credentials.json" not in gac_check:
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS not set correctly for OIDC")
        results.append("PASS: scripts().container() - GOOGLE_APPLICATION_CREDENTIALS set (OIDC)")

        # Verify GOOGLE_CLOUD_PROJECT env var is set
        project_check = await container.with_exec(["sh", "-c", "echo $GOOGLE_CLOUD_PROJECT"]).stdout()
        if project_id not in project_check:
            raise Exception("GOOGLE_CLOUD_PROJECT not set correctly")
        results.append("PASS: scripts().container() - GOOGLE_CLOUD_PROJECT set correctly")

        # Verify credentials file exists
        cred_file_check = await container.with_exec(["cat", "/tmp/gcp-credentials.json"]).stdout()
        if "external_account" not in cred_file_check:
            raise Exception("Credentials file does not contain external_account type")
        results.append("PASS: scripts().container() - WIF credentials file configured")

        # DELETE database
        await firestore.delete(gcloud=gcloud, database_id=database_id)
        results.append("PASS: DELETE - database deleted")

    except Exception as e:
        results.append(f"FAIL: {e}")
        try:
            await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
            await firestore.delete(gcloud=gcloud, database_id=database_id)
            results.append(f"CLEANUP: deleted database {database_id}")
        except Exception:
            pass
        raise

    return "\n".join(results)
