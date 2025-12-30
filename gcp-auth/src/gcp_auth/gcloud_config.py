"""Common gcloud container configuration helpers."""

import dagger
from dagger import dag


def create_base_gcloud_container(image: str = "google/cloud-sdk:alpine") -> dagger.Container:
    """Create a base gcloud SDK container."""
    return dag.container().from_(image)


def configure_gcloud_project(
    container: dagger.Container,
    project_id: str,
    region: str = "us-central1",
) -> dagger.Container:
    """Configure gcloud with project and region settings."""
    return (
        container
        .with_exec(["gcloud", "config", "set", "project", project_id])
        .with_exec(["gcloud", "config", "set", "compute/region", region])
        .with_exec(["gcloud", "config", "set", "compute/zone", f"{region}-a"])
    )


def install_gcloud_components(
    container: dagger.Container,
    components: list[str] | None,
) -> dagger.Container:
    """Install additional gcloud components."""
    if not components:
        return container

    for component in components:
        container = container.with_exec([
            "gcloud", "components", "install", component, "--quiet"
        ])

    return container


def authenticate_with_cred_file(
    container: dagger.Container,
    cred_file_path: str = "/tmp/gcp-credentials.json",
) -> dagger.Container:
    """Authenticate gcloud using a credentials file."""
    return (
        container
        # Debug: verify credentials file content before auth
        .with_exec(["sh", "-c", f"""
            echo "DEBUG: Verifying credentials file at {cred_file_path}..."
            if [ ! -f {cred_file_path} ]; then
                echo "ERROR: Credentials file not found"
                exit 1
            fi
            echo "DEBUG: File size: $(wc -c < {cred_file_path}) bytes"
            echo "DEBUG: First 200 chars of credential_source section:"
            grep -A5 '"credential_source"' {cred_file_path} | head -c 200
            echo ""
            if grep -q '"url": "https://' {cred_file_path}; then
                echo "DEBUG: URL contains https:// - OK"
            else
                echo "ERROR: URL does not contain https://"
                echo "DEBUG: Full file content:"
                cat {cred_file_path}
                exit 1
            fi
        """])
        .with_exec([
            "gcloud", "auth", "login",
            f"--cred-file={cred_file_path}"
        ])
    )
