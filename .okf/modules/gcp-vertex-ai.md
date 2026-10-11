---
type: Dagger Module
title: "gcp-vertex-ai"
description: "Deploy containerized models to Vertex AI endpoints and list models and endpoints."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-vertex-ai
tags: [module, gcp, ml]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
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
    last_modified: 2026-01-04T20:17:01+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-vertex-ai/dagger.json
    title: "gcp-vertex-ai/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
---

# Functions

| Function | Notes |
|----------|-------|
| `deploy_model(gcloud, image_uri, model_name, endpoint_name, region, machine_type, accelerator_type, accelerator_count, min_replicas, max_replicas)` | Upload + endpoint + deploy |
| `list_models(gcloud, region)` | |
| `list_endpoints(gcloud, region)` | |

Takes a pre-authenticated `gcloud` container from [gcp-auth](/modules/gcp-auth.md).[^main]
The README roadmap lists Vertex AI Agent Engine support as a planned expansion.[^module-readme]

[^main]: gcp-vertex-ai/src/gcp_vertex_ai/main.py
[^module-readme]: gcp-vertex-ai/README.md
