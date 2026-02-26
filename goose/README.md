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
| `suggest-github-fix` | Analyze a CI failure and post inline code suggestions on a GitHub PR | `str` |
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

## Self-Improvement

Pass `--self-improve` to let the agent update your context file with discoveries as it works.

| Mode | Behavior |
|------|----------|
| `off` (default) | No change to current behavior |
| `write` | Agent updates the context file (e.g. `GOOSE.md`) in the workspace |
| `commit` | Agent updates the context file and creates a git commit |

```shell
dagger call assist \
  --google-cloud-dir ~/.config/gcloud \
  --source=. \
  --self-improve=write \
  --assignment="Inspect Cloud Run services and report their status"
```

The agent appends learned context (architecture patterns, gotchas, conventions) under a `## Learned Context` heading. Existing content is never overwritten.

> **Note:** Most Goose entrypoints return `str`, so the updated context file only persists if the caller exports the workspace. The `develop-github-issue` entrypoint benefits fully since it uses the workspace for PR creation.

## Suggest Fix on CI Failure

The `suggest-github-fix` function analyzes CI pipeline failures and posts GitHub "suggested changes" directly on the PR. Developers can apply fixes with one click. This function does not require GCP authentication.

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--github-token` | GitHub token (as a Dagger secret) with `repo` permissions | Yes |
| `--pr-number` | Pull request number | Yes |
| `--repo` | GitHub repository URL (e.g. `https://github.com/owner/repo`) | Yes |
| `--commit-sha` | HEAD commit SHA of the PR branch | Yes |
| `--error-output` | CI error output (stderr/stdout) | Yes |
| `--source` | Source directory of the PR branch | No |

### CLI Usage

```shell
dagger call suggest-github-fix \
  --github-token=env:GITHUB_TOKEN \
  --pr-number=123 \
  --repo="https://github.com/owner/my-gcp-app" \
  --commit-sha="abc123" \
  --error-output="$(cat ci-output.log)" \
  --source=.
```

### GitHub Actions Workflow

Add a step to your existing CI workflow that runs on failure:

```yaml
name: CI

on:
  pull_request:

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Build and deploy
        id: deploy
        run: |
          docker build . 2>&1 | tee ci-output.log
        continue-on-error: true

      - name: Suggest fixes on failure
        if: steps.deploy.outcome == 'failure'
        uses: dagger/dagger-for-github@v7
        with:
          verb: call
          version: "latest"
          module: github.com/certainty-labs/daggerverse/goose
          args: >-
            suggest-github-fix
            --github-token=env:GITHUB_TOKEN
            --pr-number=${{ github.event.pull_request.number }}
            --repo="${{ github.server_url }}/${{ github.repository }}"
            --commit-sha=${{ github.event.pull_request.head.sha }}
            --error-output="$(cat ci-output.log)"
            --source=.
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

      - name: Fail if deploy failed
        if: steps.deploy.outcome == 'failure'
        run: exit 1
```

## GCP Documentation Search (Optional)

Pass `--developer-knowledge-api-key` to enable real-time search of Google's official developer documentation during operations.

## Dependencies

- [gcp-auth](../gcp-auth) — GCP authentication
- [gcp-cloud-run](../gcp-cloud-run) — Cloud Run operations
- [gcp-artifact-registry](../gcp-artifact-registry) — Container image publishing
- [gcp-firebase](../gcp-firebase) — Firebase Hosting deployment
- [gcp-vertex-ai](../gcp-vertex-ai) — Vertex AI model deployment
- [health-check](../health-check) — Container health checking
