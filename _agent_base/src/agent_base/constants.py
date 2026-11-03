"""Shared constants for Dagger coding agents.

Names are Python function names; `llm_helpers.tool_exclusions` turns them into
the GraphQL names that `LLM.with_tools(except_=...)` matches.
"""

# Entrypoints never offered to an LLM as tools, so an agent cannot recurse into itself
BLOCKED_ENTRYPOINTS = [
    "assist", "review", "write_tests", "build",
    "upgrade", "develop_github_issue", "suggest_github_fix",
]

# Tools that change the workspace, hidden from read-only LLMs (task sub-agent, suggest-fix)
BLOCKED_DESTRUCTIVE = ["edit_file", "write_file"]

# Valid modes for the self_improve constructor field
SELF_IMPROVE_MODES = ("off", "write", "commit")
