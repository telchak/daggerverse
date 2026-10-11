---
type: Dagger Module
title: "gcp-cloud-run"
description: "Deploy, inspect and delete Cloud Run services and jobs from a pre-authenticated gcloud container."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-cloud-run
tags: [module, gcp]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
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
    last_modified: 2026-01-04T20:17:01+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-cloud-run/dagger.json
    title: "gcp-cloud-run/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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
dagger -m gcp-cloud-run call service deploy --gcloud=... --image=... --service-name=my-svc
```

`RunService.deploy` takes port, cpu, memory, min/max instances, concurrency, timeout,
`allow_unauthenticated`, env vars, secrets, VPC connector, service account, `cpu_boost` and
`disable_invoker_iam_check` (added 2026-03-24).[^invoker] Integer inputs are validated
(`_validate_positive_int`).

# Naming

The secondary types were `CloudRunService` / `CloudRunJob` until 2026-03-05, which rendered as
`GcpCloudRunCloudRunService` on daggerverse.dev; they were renamed `RunService` / `RunJob`.[^rename-types]
`Service` alone would collide with Dagger core. See
[Daggerverse publishing](/dagger/daggerverse-publishing.md).

# History

The module was split into the two classes on 2026-01-15, and was the base of the first agent
(`gcp-cloud-run-agent`, 2026-01-23), which later became [Goose](/agents/goose.md).

[^main]: gcp-cloud-run/src/gcp_cloud_run/main.py
[^rename-types]: fix(gcp-cloud-run): rename types to avoid redundant daggerverse names
[^invoker]: feat(gcp-cloud-run): add disable-invoker-iam-check option to deploy
