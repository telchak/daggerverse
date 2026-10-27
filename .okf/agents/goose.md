---
type: AI Agent
title: "Goose (GCP operations agent)"
description: "AI GCP operations agent: deploy, troubleshoot, review, upgrade and assist across Cloud Run, Firebase Hosting, Vertex AI and Artifact Registry, with the gcloud MCP server; on agent-base since the 1.0 port."
resource: https://github.com/telchak/daggerverse/tree/main/goose
tags: [agent, llm, gcp]
generated: { by: claude-code/2.1.310, at: 2026-10-27T13:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/goose/src/goose/main.py
    title: "goose/src/goose/main.py"
    author: human:telchak
    last_modified: 2026-10-27T13:00:00Z
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/goose/README.md
    title: "goose/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/goose/src/goose/prompts
    title: "goose prompt files"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/goose/dagger-module.toml
    title: "goose/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: rename
    resource: https://github.com/telchak/daggerverse/commit/8cf276bf20c47301549ee867fa41a913f7b2ef81
    title: "feat(goose): Rename gcp-orchestrator-agent to Goose and refactor tests"
    author: human:telchak
    last_modified: 2026-02-11T20:59:22+01:00
  - id: orchestrator
    resource: https://github.com/telchak/daggerverse/commit/020b6e7d09e54c798e9511e8d64ae5f7b2258f8c
    title: "feat!: Delete gcp-cloud-run agent and add gcp-orchestrator-agent"
    author: human:telchak
    last_modified: 2026-02-07T21:03:16+01:00
  - id: gcp-marker
    resource: https://github.com/telchak/daggerverse/blob/main/goose/.agent-gcp
    title: "goose/.agent-gcp"
    author: human:telchak
    last_modified: 2026-02-11T20:59:22+01:00
---

# Entrypoints

`assist`, `review`, `deploy(assignment, service_name?, repository?)`,
`troubleshoot(issue, service_name?)`, `upgrade(service_name, target_version, dry_run)`,
`suggest_github_fix`, `develop_github_issue`. All return `str`, not a `Directory`.[^main]
Goose has no `@agent` function.

On top of the workspace tools, `mcp` and `task`, Goose exposes about 25 GCP tools wrapping its
module dependencies: Cloud Run (`deploy_service`, `describe_service`, `get_revisions`,
`check_iam_policy`, `get_service_logs`, ...), Artifact Registry (`publish_container`,
`list_images`, and `build_and_publish(ws, repository, image_name, tag, dockerfile)`, which builds
the bound workspace with its Dockerfile), Firebase (`deploy_firebase_hosting`,
`deploy_firebase_preview`, `delete_firebase_channel`, taking `ws`; their `node_version` defaults to
`"22"`, `"20"` until 2026-10-27), Vertex AI, health checks, and
Google Developer Knowledge API search (`search_gcp_docs`, `get_gcp_doc`, `batch_get_gcp_docs`,
via `developerknowledge.googleapis.com/v1alpha`, enabled by `--developer-knowledge-api-key`). The
docs API is exposed as functions, not MCP, because Dagger only supports stdio MCP servers and that
API is HTTP.[^agent-readme] Every GCP tool first resolves auth, project and region
(`_ensure_resolved`).

# Authentication (pick one)

`--gcloud` (pre-built container) | `--oidc-token` + `--workload-identity-provider` |
`--credentials` (SA key) | `--google-cloud-dir ~/.config/gcloud` (local dev).
Project and region resolve in the order **explicit arg -> `DAGGER.md` -> gcloud config ->
default** (`us-central1` for region). `DAGGER.md` lines such as `- Project ID: my-project`,
`- Region: ...`, `- Service name: ...` are parsed.[^main]

The `gcloud` MCP server (`@google-cloud/gcloud-mcp`, `live=True`) is installed on top of the
resolved gcloud container so it inherits the same auth; tasks `assist`, `troubleshoot` and
`upgrade` get it, `deploy`, `review` and `suggest_fix` do not.

# On agent-base since 1.0

The 1.0 port moved Goose onto [agent-base](/agents/agent-base.md) (workspace tools, LLM
builders, router, GitHub, MCP driver), with `include = ["../_agent_base"]` on its runtime
manifest.[^manifest] It keeps module-level `_BLOCKED_ENTRYPOINTS`, `_BLOCKED_DESTRUCTIVE` (every
deploy, delete and publish tool, including `build_and_publish`) and `_FIELDS` (its 11 constructor
fields). `main.py` is about 1300 lines, above the 600-line CI warning threshold.[^main]

# History

`gcp-cloud-run-agent` (2026-01-23) -> deleted for `gcp-orchestrator-agent`
(2026-02-07)[^orchestrator] -> renamed Goose (2026-02-11)[^rename] -> agent-base and Dagger 1.0
(2026-10-24). `.agent-gcp` marks it as needing GCP credentials in CI;[^gcp-marker]
`.agent-tests`: `assist review deploy troubleshoot upgrade`.

[^main]: goose/src/goose/main.py
[^agent-readme]: goose/README.md
[^manifest]: goose/dagger-module.toml
[^rename]: feat(goose): Rename gcp-orchestrator-agent to Goose and refactor tests
[^orchestrator]: feat!: Delete gcp-cloud-run agent and add gcp-orchestrator-agent
[^gcp-marker]: goose/.agent-gcp
