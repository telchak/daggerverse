# Goose

AI-powered GCP deployment, troubleshooting, and operations agent using the Dagger LLM API. Supports Cloud Run, Firebase Hosting, Vertex AI, and health checks.

## Installation

```shell
dagger install github.com/certainty-labs/daggerverse/goose@<version>
```

## Features

- **Multi-service deployment**: Cloud Run, Firebase Hosting, Vertex AI
- **Operations assistant**: Inspect infrastructure, plan deployments, answer GCP questions
- **Config review**: Audit Dockerfiles, firebase.json, cloudbuild.yaml for best practices
- **Service upgrades**: Update versions, configs, traffic splits
- **Troubleshooting**: AI-powered diagnostics across all supported services
- **GitHub integration**: Read issues, route to the best function, create PRs
- **Simplified auth**: One set of credentials for gcloud + Firebase
- **Auto-discovery**: project_id and region extracted from gcloud config when omitted
- **DAGGER.md support**: Per-repo context files that customize agent behavior
- **GCP docs search**: Optional real-time search of Google's official developer documentation
- **Workspace tools**: Read, edit, and search deployment configs
- **Sub-agent**: Delegate research tasks to a focused sub-agent

## Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `assist` | General GCP ops assistant: inspect infra, plan deployments, answer questions | `str` |
| `review` | Review deployment configs for best practices and security | `str` |
| `deploy` | Deploy a service (Cloud Run, Firebase, or Vertex AI) | `str` |
| `troubleshoot` | Diagnose issues, read logs, inspect services | `str` |
| `upgrade` | Upgrade a service version, config, or traffic split | `str` |
| `develop-github-issue` | Read issue, route to best function, create PR | `str` |
| `task` | Launch a sub-agent for research or focused work | `str` |

## Quick Start

### Option 1: OIDC / Workload Identity Federation (recommended for CI/CD)

```shell
dagger call deploy \
  --oidc-token=env:OIDC_TOKEN \
  --workload-identity-provider="projects/PROJECT_NUM/locations/global/workloadIdentityPools/POOL/providers/PROVIDER" \
  --service-account-email="sa@project.iam.gserviceaccount.com" \
  --project-id=my-project \
  --source=. \
  --assignment="Deploy to Cloud Run, allow unauthenticated access"
```

### Option 2: Service Account JSON key

```shell
dagger call deploy \
  --credentials=file:./service-account.json \
  --source=. \
  --assignment="Deploy to Firebase Hosting"
```

### Option 3: Host gcloud config (local development)

```shell
dagger call deploy \
  --google-cloud-dir ~/.config/gcloud \
  --source=. \
  --assignment="Deploy to Cloud Run, allow unauthenticated access"
```

### Option 4: Pre-built gcloud container (backward compatible)

```shell
dagger call deploy \
  --gcloud=<authenticated-container> \
  --project-id=my-project \
  --service-name=my-service \
  --assignment="Deploy gcr.io/google-samples/hello-app:1.0, allow unauthenticated access"
```

### Operations Assistant

```shell
dagger call assist \
  --google-cloud-dir ~/.config/gcloud \
  --source=. \
  --assignment="List all Cloud Run services and their current revision status"
```

### Config Review

```shell
dagger call review \
  --google-cloud-dir ~/.config/gcloud \
  --source=. \
  --focus="security"
```

### Service Upgrade

```shell
dagger call upgrade \
  --google-cloud-dir ~/.config/gcloud \
  --service-name=my-api \
  --target-version="gcr.io/my-project/my-api:v2.0" \
  --dry-run
```

### Troubleshooting

```shell
dagger call troubleshoot \
  --google-cloud-dir ~/.config/gcloud \
  --service-name=my-service \
  --issue="Service returns 503 errors intermittently"
```

## Authentication

The agent supports four authentication paths. For OIDC and SA JSON, one set of credentials is used for both gcloud operations and Firebase Hosting.

| Scenario | Flags needed |
|----------|-------------|
| OIDC/WIF (CI/CD) | `--oidc-token` + `--workload-identity-provider` + `--project-id` |
| SA JSON key | `--credentials` (project_id auto-extracted) |
| Host gcloud (local dev) | `--google-cloud-dir ~/.config/gcloud` (project_id/region auto-discovered) |
| Pre-built gcloud | `--gcloud` + `--project-id` |

## Context Files

Create a context file in your repository root to customize agent behavior. Goose looks for these files in order (first found wins):

1. `GOOSE.md` — Goose-specific context
2. `DAGGER.md` — General Dagger agent context (backward compatible)
3. `AGENT.md` — Generic agent context
4. `CLAUDE.md` — Claude-style context

### Parsed fields (from DAGGER.md)

| Field | Key | Example |
|-------|-----|---------|
| project_id | `Project ID:` | `my-project` |
| region | `Region:` | `us-central1` |
| service_name | `Service name:` | `my-api` |

### Priority order

**explicit CLI flags > context file > gcloud config > defaults**

## GCP Documentation Search (Optional)

Pass `--developer-knowledge-api-key` to enable real-time search of Google's official developer documentation during operations.

## Dependencies

- [gcp-auth](../gcp-auth) — GCP authentication
- [gcp-cloud-run](../gcp-cloud-run) — Cloud Run operations
- [gcp-artifact-registry](../gcp-artifact-registry) — Container image publishing
- [gcp-firebase](../gcp-firebase) — Firebase Hosting deployment
- [gcp-vertex-ai](../gcp-vertex-ai) — Vertex AI model deployment
- [health-check](../health-check) — Container health checking
