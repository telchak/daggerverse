# Agent patterns

Cross-cutting design patterns shared by the agents.

* [Agent anatomy](agent-anatomy.md) - The common shape of every daggerverse AI agent in Dagger 1.0: a Dagger object on the Python SDK runtime with LLM entrypoints, workspace tools, an mcp tool, prompts, an optional @agent function and GitHub integration.
* [Blocked functions](blocked-functions.md) - Which of an agent's own functions and fields are excluded from its LLM tool set (with_tools except_), why the names must be camelCase, and the rule that only functions that exist may be listed.
* [Context files and self-improvement](context-files-and-self-improvement.md) - How agents read per-repo context (AGENT-specific file + AGENTS.md) and, with --self-improve, write learned context back.
* [develop-github-issue (issue to PR)](develop-github-issue.md) - Entry point that reads a GitHub issue, routes it with a classification LLM to the best agent function, runs it, and opens a pull request.
* [Exploration budget in prompts](exploration-budget.md) - System prompts cap agents at about 15 tool calls and forbid reading every file, to stop CI exploration spirals and timeouts.
* [LLM results and fallbacks](llm-output-binding.md) - How agents read results in Dagger 1.0 (final reply or edited workspace, after loop), the JSON replies of routers and suggest-fix, and the retry when a routed call changes nothing; formerly Env output bindings.
* [suggest-github-fix (self-healing CI)](suggest-github-fix.md) - Entry point that analyzes a CI failure, gets fix suggestions from a read-only LLM as JSON, and posts them as inline GitHub suggestion comments on the PR; AI runs only when deterministic checks fail.
* [Task-scoped MCP servers](task-scoped-mcp.md) - Agents attach MCP servers (and experimental MCP tools) only to the entrypoints that benefit, list their tools in the system prompt and call them through an mcp tool.
