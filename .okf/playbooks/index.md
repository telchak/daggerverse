# Playbooks

Step-by-step procedures for recurring tasks.

* [Add a new AI agent](add-a-new-agent.md) - Steps to create a new coding agent on top of _agent_base, with prompts, tests and CI wiring.
* [Add a new module](add-a-new-module.md) - Steps to add a Dagger module to this monorepo so CI discovers, validates, tests and releases it.
* [Debug an agent test that times out in CI](debug-agent-ci-timeout.md) - An agent CI job that dies at exactly 20 minutes with no traceback usually means an MCP service never started or the agent looped.
* [Run tests locally](run-tests-locally.md) - Commands to run the tests module locally, with and without GCP or LLM credentials.
* [Upgrade the Dagger engine version](upgrade-dagger-engine.md) - How a Dagger engine bump flows through Renovate, the self-hosted runner label, dagger.json files and CI.
