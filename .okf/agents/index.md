# Agents

The AI agents and the shared agent library.

* [_agent_base (shared agent library)](agent-base.md) - The shared Python package that holds workspace tools, LLM builders, the MCP stdio driver, GitHub integration and router logic for all five agents.
* [Angie (Angular agent)](angie.md) - AI Angular development agent: assist, review, write tests, build and upgrade Angular projects, with the Angular CLI MCP server and an @agent function for dagger agent.
* [Daggie (Dagger CI specialist agent)](daggie.md) - AI agent that creates, explains, debugs and reviews Dagger 1.0 (and 0.x) modules and pipelines across SDKs, backed by dagger-mcp and runtime-cloned reference modules.
* [Goose (GCP operations agent)](goose.md) - AI GCP operations agent: deploy, troubleshoot, review, upgrade and assist across Cloud Run, Firebase Hosting, Vertex AI and Artifact Registry, with the gcloud MCP server; on agent-base since the 1.0 port.
* [Monty (Python agent)](monty.md) - AI Python development agent: assist, review, write tests, build/lint/typecheck and upgrade dependencies, with python-lft and pypi-query MCP servers and an @agent function.
* [Speck (spec-driven development agent)](speck.md) - AI agent that turns a prompt or GitHub issue into a spec, a technical plan, and a JSON task decomposition assigning agents and models, designed for GitHub Actions matrices.
