---
type: Dagger Module
title: "gcp-vertex-ai"
description: "Deploy containerized models to Vertex AI endpoints and list models and endpoints."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-vertex-ai
tags: [module, gcp, ml]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-vertex-ai/src/gcp_vertex_ai/main.py
    title: "gcp-vertex-ai/src/gcp_vertex_ai/main.py"
    author: human:telchak
    last_modified: 2026-02-17T10:31:33+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-vertex-ai/README.md
    title: "gcp-vertex-ai/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-vertex-ai/dagger-module.toml
    title: "gcp-vertex-ai/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Roadmap"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Functions

| Function | Notes |
|----------|-------|
| `deploy_model(gcloud, image_uri, model_name, endpoint_name, region, machine_type, accelerator_type, accelerator_count, min_replicas, max_replicas)` | Upload + endpoint + deploy |
| `list_models(gcloud, region)` | |
| `list_endpoints(gcloud, region)` | |

Takes a pre-authenticated `gcloud` container from [gcp-auth](/modules/gcp-auth.md).[^main] [^module-readme]
The repository README's roadmap lists Vertex AI Agent Engine support as a planned expansion.[^readme]

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: gcp-vertex-ai/src/gcp_vertex_ai/main.py
[^module-readme]: gcp-vertex-ai/README.md
[^manifest]: gcp-vertex-ai/dagger-module.toml
[^readme]: Repository README, Roadmap
