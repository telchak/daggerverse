---
type: AI Agent
title: "Goose (GCP operations agent)"
description: "AI GCP operations agent: deploy, troubleshoot, review, upgrade and assist across Cloud Run, Firebase Hosting, Vertex AI and Artifact Registry, with the gcloud MCP server."
resource: https://github.com/telchak/daggerverse/tree/main/goose
tags: [agent, llm, gcp]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/goose/src/goose/main.py
    title: "goose/src/goose/main.py"
    author: human:telchak
    last_modified: 2026-02-28T16:53:12+01:00
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/goose/README.md
    title: "goose/README.md"
    author: human:telchak
    last_modified: 2026-03-01T14:43:35+01:00
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/goose/src/goose/prompts
    title: "goose prompt files"
    author: human:telchak
    last_modified: 2026-02-21T21:46:12+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/goose/dagger.json
    title: "goose/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
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
  - id: ctx
    resource: https://github.com/telchak/daggerverse/commit/03a8a4c16d754dfccb3dacd4b17355c5f7b9e63f
    title: "feat(goose): Apply context engineering refactoring"
    author: human:telchak
    last_modified: 2026-02-16T00:47:23+01:00
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

On top of workspace tools Goose exposes ~25 GCP tools wrapping its module dependencies:
Cloud Run (`deploy_service`, `describe_service`, `get_revisions`, `check_iam_policy`,
`get_service_logs`, ...), Artifact Registry (`publish_container`, `list_images`), Firebase
(`deploy_firebase_hosting`, `deploy_firebase_preview`, `delete_firebase_channel`), Vertex AI,
health checks, and Google Developer Knowledge API search (`search_gcp_docs`, `get_gcp_doc`,
`batch_get_gcp_docs`, via `developerknowledge.googleapis.com/v1alpha`, enabled by
`--developer-knowledge-api-key`). The docs API is exposed as functions, not MCP, because Dagger
only supports stdio MCP servers and that API is HTTP.[^agent-readme]

# Authentication (pick one)

`--gcloud` (pre-built container) | `--oidc-token` + `--workload-identity-provider` |
`--credentials` (SA key) | `--google-cloud-dir ~/.config/gcloud` (local dev).
Project and region resolve in the order **explicit arg -> `DAGGER.md` -> gcloud config ->
default** (`us-central1` for region). `DAGGER.md` lines such as `- Project ID: my-project`,
`- Region: ...`, `- Service name: ...` are parsed.[^main]

The `gcloud` MCP server (`@google-cloud/gcloud-mcp`) is installed on top of the resolved gcloud
container so it inherits the same auth.

# Not on agent-base

Goose predates [agent-base](/agents/agent-base.md) and keeps its own `_BLOCKED_ENTRYPOINTS`,
`_BLOCKED_DESTRUCTIVE` (which adds every deploy/delete/publish tool), self-improve prompt,
router parser and `_get_result_or_last_reply`. `main.py` is ~1500 lines, well above the
600-line CI warning threshold.[^main] Changes to shared agent behaviour must be ported by hand.

# History

`gcp-cloud-run-agent` (2026-01-23) -> deleted for `gcp-orchestrator-agent`
(2026-02-07)[^orchestrator] -> renamed Goose (2026-02-11).[^rename] `.agent-gcp` marks it as
needing GCP credentials in CI;[^gcp-marker] `.agent-tests`: `assist review deploy troubleshoot upgrade`.

[^main]: goose/src/goose/main.py
[^agent-readme]: goose/README.md
[^rename]: feat(goose): Rename gcp-orchestrator-agent to Goose and refactor tests
[^orchestrator]: feat!: Delete gcp-cloud-run agent and add gcp-orchestrator-agent
[^gcp-marker]: goose/.agent-gcp
