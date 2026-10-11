# Decisions

Why things are the way they are, reconstructed from commit history.

* [AI agents run only when deterministic checks fail](ai-on-failure-only.md) - The normal CI path is deterministic Dagger checks; coding agents are invoked from the workflow only on failure, to suggest fixes. *(draft)*
* [Bundle a lockfile-backed Angular fixture for module tests](bundled-angular-test-fixture.md) - The angular module test builds a small committed Angular 21 app with package-lock.json instead of cloning the RealWorld example.
* [Centralize tests in one tests module](centralized-tests-module.md) - Tests live in tests/ and call modules through their public Dagger API, rather than inside each module.
* [GCP service modules accept pre-authenticated inputs](decouple-gcp-modules-from-gcp-auth.md) - gcp-artifact-registry, gcp-cloud-run, gcp-vertex-ai and gcp-firebase take a gcloud container or token instead of depending on gcp-auth.
* [Give agents deterministic build modules](deterministic-build-modules-for-agents.md) - Angular and Python agents call dedicated non-LLM modules (angular, python-build) for build, lint, test, so the reliable path never depends on the model.
* [Gemini as the CI LLM provider](gemini-as-ci-llm.md) - Agent tests in CI run on Gemini (GEMINI_API_KEY, vars.GEMINI_MODEL) since 2026-02-17, after starting on Anthropic.
* [Native OIDC in Dagger instead of google-github-actions/auth](native-oidc-instead-of-google-github-actions-auth.md) - GCP authentication in CI is done inside Dagger modules from the GitHub OIDC request token, with no external auth Action.
* [Per-module semver tags instead of a repo CalVer release](per-module-semver-tags.md) - Each module is released as <module>/vX.Y.Z from Conventional Commits; the repo-wide CalVer GitHub release was dropped.
* [Pin mcp<2 for Python MCP servers (temporary)](pin-mcp-below-2.md) - dagger-mcp and Monty's python-lft server install mcp<2 because mcp 2.0.0 removed mcp.server.fastmcp; remove once ported.
* [Use relative paths for in-repo module dependencies](relative-paths-for-monorepo-dependencies.md) - In-repo dagger.json dependencies use ../<module> paths, not github.com URLs; tried and reverted on 2026-01-04.
* [Self-hosted ARC runners labelled by Dagger version](self-hosted-dagger-runners.md) - CI jobs run on self-hosted Actions Runner Controller runners labelled dagger-v<version> instead of ubuntu-latest with engine-cache restore.
* [Extract shared agent logic into _agent_base](shared-agent-base-package.md) - Duplicated workspace, LLM, GitHub and routing code was moved into an included Python package so each agent is a thin wrapper.
