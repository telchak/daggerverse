# Modules

One concept per reusable (non-agent) Dagger module.

* [angular](angular.md) - Deterministic Angular build, lint, test, serve and install functions; the non-LLM backbone used by the Angie agent.
* [calver](calver.md) - Calendar Versioning: generate date-based version strings, optionally auto-incrementing MICRO from git tags.
* [dagger-mcp](dagger-mcp.md) - An MCP server, run as a privileged-nested Dagger service, that lets an LLM introspect the live Dagger engine schema, run GraphQL and read SDK guides.
* [gcp-artifact-registry](gcp-artifact-registry.md) - Publish and manage container images and generic artifacts in Google Artifact Registry.
* [gcp-auth](gcp-auth.md) - GCP authentication for Dagger pipelines: authenticated gcloud containers and access tokens from OIDC/WIF, service account keys or host ADC.
* [gcp-cloud-run](gcp-cloud-run.md) - Deploy, inspect and delete Cloud Run services and jobs from a pre-authenticated gcloud container.
* [gcp-firebase](gcp-firebase.md) - Firebase Hosting build/deploy/preview channels, Firestore database management, and script runners with Firebase credentials.
* [gcp-vertex-ai](gcp-vertex-ai.md) - Deploy containerized models to Vertex AI endpoints and list models and endpoints.
* [health-check](health-check.md) - Container health checks (HTTP, TCP, exec, readiness) using Dagger service bindings.
* [oidc-token](oidc-token.md) - CI-agnostic OIDC JWT handling: fetch from GitHub Actions, pass through GitLab CI and CircleCI tokens, decode claims.
* [python-build](python-build.md) - Deterministic Python build, lint (ruff/flake8/pylint), test, typecheck (mypy/pyright) and install functions; the non-LLM backbone used by Monty.
* [semver](semver.md) - Semantic Versioning driven by Conventional Commits, with monorepo tag prefixes; the engine behind this repository's releases.
