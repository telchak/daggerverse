---
type: Dagger Module
title: "gcp-artifact-registry"
description: "Publish and manage container images and generic artifacts in Google Artifact Registry."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-artifact-registry
tags: [module, gcp]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
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
    last_modified: 2026-02-16T00:47:23+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-artifact-registry/dagger.json
    title: "gcp-artifact-registry/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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

`docker_config` (added 2026-02-13) lets the caller supply registry auth instead of a gcloud
container.[^docker-config] Region defaults to `us-central1`.[^main] CI passes
`--repository=${{ secrets.GCP_ARTIFACT_REGISTRY_REPOSITORY }}` to its test.

[^main]: gcp-artifact-registry/src/gcp_artifact_registry/main.py
[^docker-config]: feat(gcp-artifact-registry): Add docker_config option to publish
