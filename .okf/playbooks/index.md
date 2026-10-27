# Playbooks

Step-by-step procedures for recurring tasks.

* [Add a new AI agent](add-a-new-agent.md) - Steps to create a new coding agent on top of _agent_base on Dagger 1.0: runtime scope, clients, shared base, prompts, tests and CI wiring.
* [Add a new module](add-a-new-module.md) - Steps to add a Dagger 1.0 module to this monorepo (scope, generated code, tests) so CI discovers, validates, checks, tests and releases it.
* [Debug an agent test that times out in CI](debug-agent-ci-timeout.md) - An agent CI job that dies at exactly 20 minutes with no traceback usually means a hung MCP session, an agent loop or an LLM provider problem; CI's buffered output hides which.
* [Run tests locally](run-tests-locally.md) - Commands to run the workspace check and the tests module locally on Dagger 1.0, with and without GCP or LLM credentials.
* [Upgrade the Dagger engine version](upgrade-dagger-engine.md) - How a Dagger version bump flows on Dagger 1.0: Renovate's grouped PR, the self-hosted runner label, regenerated code, the few hand edits and the full CI.
