---
okf_version: "0.2"
---

# telchak/daggerverse knowledge bundle

Shared, versioned knowledge about this repository for humans and coding agents, in
[Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format) v0.2.
Read this index first, then follow links only into what your task needs. Every concept
carries `generated`, `sources` and `stale_after`; none is `verified` yet, so treat claims
as "check before relying on this" and confirm against the code. History of the bundle is in
[log.md](log.md). How to maintain it is in the repository-root `CLAUDE.md`.

# Overview

* [Overview](overview/) - Start here: what the repository is and how its modules relate.
  * [telchak/daggerverse](overview/repository.md)
  * [Module dependency graph](overview/dependency-graph.md)

# Modules

* [Modules](modules/) - One concept per reusable (non-agent) Dagger module.
  * [angular](modules/angular.md)
  * [calver](modules/calver.md)
  * [dagger-mcp](modules/dagger-mcp.md)
  * [gcp-artifact-registry](modules/gcp-artifact-registry.md)
  * [gcp-auth](modules/gcp-auth.md)
  * [gcp-cloud-run](modules/gcp-cloud-run.md)
  * [gcp-firebase](modules/gcp-firebase.md)
  * [gcp-vertex-ai](modules/gcp-vertex-ai.md)
  * [health-check](modules/health-check.md)
  * [oidc-token](modules/oidc-token.md)
  * [python-build](modules/python-build.md)
  * [semver](modules/semver.md)

# Agents

* [Agents](agents/) - The AI agents and the shared agent library.
  * [_agent_base (shared agent library)](agents/agent-base.md)
  * [Angie (Angular agent)](agents/angie.md)
  * [Daggie (Dagger CI specialist agent)](agents/daggie.md)
  * [Goose (GCP operations agent)](agents/goose.md)
  * [Monty (Python agent)](agents/monty.md)
  * [Speck (spec-driven development agent)](agents/speck.md)

# Agent patterns

* [Agent patterns](patterns/) - Cross-cutting design patterns shared by the agents.
  * [Agent anatomy](patterns/agent-anatomy.md)
  * [Blocked functions](patterns/blocked-functions.md)
  * [Context files and self-improvement](patterns/context-files-and-self-improvement.md)
  * [develop-github-issue (issue to PR)](patterns/develop-github-issue.md)
  * [Exploration budget in prompts](patterns/exploration-budget.md)
  * [LLM results and fallbacks](patterns/llm-output-binding.md)
  * [suggest-github-fix (self-healing CI)](patterns/suggest-github-fix.md)
  * [Task-scoped MCP servers](patterns/task-scoped-mcp.md)

# Infrastructure

* [Infrastructure](infrastructure/) - CI, releases, tests module, Renovate and SonarCloud.
  * [CI pipeline (ci.yml)](infrastructure/ci-pipeline.md)
  * [Release process (per-module semver tags)](infrastructure/release-process.md)
  * [Renovate configuration](infrastructure/renovate.md)
  * [SonarCloud quality gate](infrastructure/sonarcloud.md)
  * [tests (centralized test module)](infrastructure/tests-module.md)

# Conventions

* [Conventions](conventions/) - How code, commits and modules are written here, and known doc drift.
  * [Cache busting for time-sensitive operations](conventions/cache-busting.md)
  * [Conventional Commits](conventions/conventional-commits.md)
  * [Documentation drift](conventions/documentation-drift.md)
  * [Module anatomy and required files](conventions/module-anatomy.md)
  * [Python SDK conventions in this repo](conventions/python-sdk.md)

# Decisions

* [Decisions](decisions/) - Why things are the way they are, reconstructed from commit history.
  * [AI agents run only when deterministic checks fail](decisions/ai-on-failure-only.md) *(draft)*
  * [Bundle a lockfile-backed Angular fixture for module tests](decisions/bundled-angular-test-fixture.md)
  * [Centralize tests in one tests module](decisions/centralized-tests-module.md)
  * [GCP service modules accept pre-authenticated inputs](decisions/decouple-gcp-modules-from-gcp-auth.md)
  * [Give agents deterministic build modules](decisions/deterministic-build-modules-for-agents.md)
  * [Gemini as the CI LLM provider](decisions/gemini-as-ci-llm.md)
  * [Call MCP servers through a one-shot stdio driver (temporary)](decisions/mcp-exec-driver.md)
  * [Migrate every module to Dagger 1.0 (beta)](decisions/migrate-to-dagger-1-0.md)
  * [Native OIDC in Dagger instead of google-github-actions/auth](decisions/native-oidc-instead-of-google-github-actions-auth.md)
  * [Per-module semver tags instead of a repo CalVer release](decisions/per-module-semver-tags.md)
  * [Pin mcp<2 for Python MCP servers (temporary)](decisions/pin-mcp-below-2.md)
  * [Use relative paths for in-repo module dependencies](decisions/relative-paths-for-monorepo-dependencies.md)
  * [Self-hosted ARC runners labelled by Dagger version](decisions/self-hosted-dagger-runners.md)
  * [Extract shared agent logic into _agent_base](decisions/shared-agent-base-package.md)

# Dagger platform

* [Dagger platform](dagger/) - Upstream Dagger knowledge this repo depends on, pinned to v1.0.0-beta.21.
  * [Dagger releases and breaking changes relevant here](dagger/breaking-changes.md)
  * [Checks, generators and installed modules (0.x toolchains)](dagger/checks-and-toolchains.md)
  * [Dagger 1.0 workspaces (dagger.toml, dagger.lock, dagger-module.toml)](dagger/dagger-1-0-workspaces.md)
  * [Publishing on daggerverse.dev](dagger/daggerverse-publishing.md)
  * [Running Dagger in GitHub Actions](dagger/github-actions-integration.md)
  * [Dagger 1.0 beta known issues](dagger/known-issues-1-0-beta.md)
  * [Dagger LLM, workspace agents and MCP](dagger/llm-and-mcp.md)
  * [Dagger modules, dependencies and the Daggerverse install path](dagger/module-system.md)
  * [Dagger platform overview](dagger/platform.md)

# Playbooks

* [Playbooks](playbooks/) - Step-by-step procedures for recurring tasks.
  * [Add a new AI agent](playbooks/add-a-new-agent.md)
  * [Add a new module](playbooks/add-a-new-module.md)
  * [Debug an agent test that times out in CI](playbooks/debug-agent-ci-timeout.md)
  * [Run tests locally](playbooks/run-tests-locally.md)
  * [Upgrade the Dagger engine version](playbooks/upgrade-dagger-engine.md)

# References

* [References](references/) - External sources, including the maintainer's article series.
  * [CI/CD in the Era of AI and Platform Engineering: A Deep Dive into Dagger CI](references/dev-to-article-series.md) *(draft)*
  * [Primary external sources](references/external-sources.md)
