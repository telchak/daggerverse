---
type: Dagger Module
title: "gcp-artifact-registry"
description: "Publish and manage container images and generic artifacts in Google Artifact Registry."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-artifact-registry
tags: [module, gcp]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-artifact-registry/src/gcp_artifact_registry/main.py
    title: "gcp-artifact-registry/src/gcp_artifact_registry/main.py"
    author: human:telchak
    last_modified: 2026-02-24T17:48:28+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-artifact-registry/README.md
    title: "gcp-artifact-registry/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-artifact-registry/dagger-module.toml
    title: "gcp-artifact-registry/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: docker-config
    resource: https://github.com/telchak/daggerverse/commit/3c3fb425d9359c72cbd0d88af83a50dba21757e7
    title: "feat(gcp-artifact-registry): Add docker_config option to publish"
    author: human:telchak
    last_modified: 2026-02-16T00:47:23+01:00
---

# Functions

| Function | Notes |
|----------|-------|
| `publish(container, project_id, repository, image_name, region, tag, gcloud?, docker_config?)` | Publishes and returns the image URI |
| `create_repository(gcloud, repository, region, format, description)` | |
| `list_images(gcloud, project_id, repository, region)` | |
| `get_image_uri(project_id, repository, image_name, region, tag)` | Pure string construction: `<region>-docker.pkg.dev/<project>/<repo>/<image>:<tag>` |
| `upload_generic(gcloud, directory, project_id, repository, package_name, version, region, file_pattern)` | Generic (non-Docker) repositories |

The `gcloud` input is a pre-authenticated container from [gcp-auth](/modules/gcp-auth.md).[^module-readme]
`docker_config` (added 2026-02-13) lets the caller supply registry auth instead of a gcloud
container, e.g. a local `~/.docker/config.json`.[^docker-config] Region defaults to
`us-central1`.[^main] CI passes `--repository=${{ secrets.GCP_ARTIFACT_REGISTRY_REPOSITORY }}`
to its test.

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: gcp-artifact-registry/src/gcp_artifact_registry/main.py
[^module-readme]: gcp-artifact-registry/README.md
[^manifest]: gcp-artifact-registry/dagger-module.toml
[^docker-config]: feat(gcp-artifact-registry): Add docker_config option to publish
