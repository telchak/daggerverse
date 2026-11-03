---
type: Dagger Module
title: "gcp-cloud-run"
description: "Deploy, inspect and delete Cloud Run services and jobs from a pre-authenticated gcloud container."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-cloud-run
tags: [module, gcp]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-cloud-run/src/gcp_cloud_run/main.py
    title: "gcp-cloud-run/src/gcp_cloud_run/main.py"
    author: human:telchak
    last_modified: 2026-03-24T23:57:54+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-cloud-run/README.md
    title: "gcp-cloud-run/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-cloud-run/dagger-module.toml
    title: "gcp-cloud-run/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: rename-types
    resource: https://github.com/telchak/daggerverse/commit/58cb609291099603c16b3154dbbae46f2784f431
    title: "fix(gcp-cloud-run): rename types to avoid redundant daggerverse names"
    author: human:telchak
    last_modified: 2026-03-05T18:54:49+01:00
  - id: invoker
    resource: https://github.com/telchak/daggerverse/commit/e5286103e153dabe450028e84a53ca423cb6b2fe
    title: "feat(gcp-cloud-run): add disable-invoker-iam-check option to deploy"
    author: human:telchak
    last_modified: 2026-03-24T23:57:54+01:00
---

# API shape

The main class exposes two sub-objects:[^main]

- `service()` -> `RunService`: `deploy`, `delete`, `get_url`, `exists`, `get_logs`
- `job()` -> `RunJob`: `deploy`, `execute`, `delete`, `get_logs`

```bash
dagger api call -m ./gcp-cloud-run service deploy --gcloud=... --image=... --service-name=my-svc
```

`RunService.deploy` takes port, cpu, memory, min/max instances, concurrency, timeout,
`allow_unauthenticated`, env vars, secrets, VPC connector, service account, `cpu_boost` and
`disable_invoker_iam_check` (added 2026-03-24).[^invoker] Integer inputs are validated
(`_validate_positive_int`).

The module README documents this shape (`service deploy`, `service get-url`, `job execute`); until
the 1.0 migration it showed flat `deploy-service` / `get-service-url` calls that never
existed.[^module-readme]

# Naming

The secondary types were `CloudRunService` / `CloudRunJob` until 2026-03-05, which rendered as
`GcpCloudRunCloudRunService` on daggerverse.dev; they were renamed `RunService` / `RunJob`.[^rename-types]
`Service` alone would collide with Dagger core. See
[Daggerverse publishing](/dagger/daggerverse-publishing.md).

# History

The module was split into the two classes on 2026-01-15, and was the base of the first agent
(`gcp-cloud-run-agent`, 2026-01-23), which later became [Goose](/agents/goose.md).

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: gcp-cloud-run/src/gcp_cloud_run/main.py
[^module-readme]: gcp-cloud-run/README.md
[^manifest]: gcp-cloud-run/dagger-module.toml
[^rename-types]: fix(gcp-cloud-run): rename types to avoid redundant daggerverse names
[^invoker]: feat(gcp-cloud-run): add disable-invoker-iam-check option to deploy
