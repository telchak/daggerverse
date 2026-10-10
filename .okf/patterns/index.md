# Agent patterns

Cross-cutting design patterns shared by the agents.

* [Agent anatomy](agent-anatomy.md) - The common shape of every daggerverse AI agent: a Dagger object with LLM entrypoints, workspace tools, prompts, MCP services and GitHub integration.
* [Blocked functions](blocked-functions.md) - Why and how agents call with_blocked_function, and the rule that only functions that exist on the class may be blocked.
* [Context files and self-improvement](context-files-and-self-improvement.md) - How agents read per-repo context (AGENT-specific file + AGENTS.md) and, with --self-improve, write learned context back.
* [develop-github-issue (issue to PR)](develop-github-issue.md) - Entry point that reads a GitHub issue, routes it with a classification LLM to the best agent function, runs it, and opens a pull request.
* [Exploration budget in prompts](exploration-budget.md) - System prompts cap agents at about 15 tool calls and forbid reading every file, to stop CI exploration spirals and timeouts.
* [LLM output binding and fallbacks](llm-output-binding.md) - Agents declare a `result` output on the Env and must make the model set it; helpers fall back to last_reply, and routed calls retry when nothing changed.
* [suggest-github-fix (self-healing CI)](suggest-github-fix.md) - Entry point that analyzes a CI failure and posts inline GitHub suggestion comments on the PR; AI runs only when deterministic checks fail.
* [Task-scoped MCP servers](task-scoped-mcp.md) - Agents attach MCP servers (and experimental MCP tools) only to the entrypoints that benefit, to save startup time and avoid confusing the model.
