"""Tests for gcp-firebase module."""

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
    """Run gcp-firebase module tests (Hosting + Firestore + Scripts)."""
    results = []
    channel_id = f"dagger-test-{int(time.time())}"
    database_id = f"dagger-test-{int(time.time())}"

    # Get gcloud container from gcp-auth
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
    )

    # Get credentials for scripts (full JSON credentials, not just access token)
    credentials = dag.gcp_auth().oidc_credentials(
        workload_identity_provider=workload_identity_provider,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
    )

    # Get access token for Firebase CLI
    token_output = await gcloud.with_exec(["gcloud", "auth", "print-access-token"]).stdout()
    access_token = dag.set_secret("firebase_token", token_output.strip())

    # Clone firebase-dagger-template from GitHub
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()

    # Load test fixtures for scripts tests (relative to module source)
    scripts_source = dag.current_module().source().directory(FIXTURES_PATH)

    firebase = dag.gcp_firebase()

    # ========== HOSTING TESTS ==========
    results.append("--- Firebase Hosting ---")

    # Test build
    dist = firebase.build(source=source)
    entries = await dist.entries()
    if len(entries) == 0:
        raise ValueError("Build produced no output files")
    results.append(f"PASS: build -> {len(entries)} files")

    try:
        # Test deploy_preview
        preview_url = await firebase.deploy_preview(
            access_token=access_token, project_id=project_id,
            channel_id=channel_id, source=source,
        )
        if not preview_url.startswith("https://"):
            raise ValueError(f"Invalid preview URL: {preview_url}")
        results.append(f"PASS: deploy_preview -> {preview_url}")

        # Test delete_channel
        await firebase.delete_channel(
            access_token=access_token, project_id=project_id, channel_id=channel_id,
        )
        results.append("PASS: delete_channel")

    except Exception as e:
        results.append(f"FAIL: {e}")
        try:
            await firebase.delete_channel(
                access_token=access_token, project_id=project_id, channel_id=channel_id,
            )
            results.append(f"CLEANUP: deleted channel {channel_id}")
        except Exception:
            pass
        raise

    # ========== FIRESTORE TESTS ==========
    results.append("--- Firestore ---")

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

        # ========== SCRIPTS TESTS ==========
        # Test scripts() credential mounting (actual script execution with OIDC
        # credentials has compatibility issues - works with service account keys)
        results.append("--- Scripts ---")

        scripts = firebase.scripts()

        # Test scripts().container() - verify credential mounting works
        container = scripts.container(
            credentials=credentials,
            source=scripts_source,
            base_image="alpine:latest",
        )
        # Verify credentials are properly mounted
        creds_check = await container.with_exec(["cat", "/tmp/gcp-credentials.json"]).stdout()
        if "type" not in creds_check:
            raise Exception("Credentials not properly mounted in container")
        results.append("PASS: scripts().container() - credentials mounted correctly")

        # Verify GOOGLE_APPLICATION_CREDENTIALS env var is set
        env_check = await container.with_exec(["sh", "-c", "echo $GOOGLE_APPLICATION_CREDENTIALS"]).stdout()
        if "/tmp/gcp-credentials.json" not in env_check:
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS not set correctly")
        results.append("PASS: scripts().container() - GOOGLE_APPLICATION_CREDENTIALS set correctly")

        # NOTE: scripts().node() and scripts().python() tests are skipped in CI
        # because OIDC credentials from oidc_credentials() don't work when extracted
        # and used in a separate container. These work with service account JSON keys.
        # TODO: Add integration tests with service account credentials

        # DELETE
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
