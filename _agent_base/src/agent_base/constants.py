"""Shared constants for Dagger coding agents."""

# Entrypoints blocked on all LLMs to prevent recursion
BLOCKED_ENTRYPOINTS = [
    "assist", "review", "write_tests", "build",
    "upgrade", "develop_github_issue", "suggest_github_fix",
]

# Destructive tools blocked on read-only sub-agents
BLOCKED_DESTRUCTIVE = ["edit_file", "write_file", "suggest_github_pr_code_comment"]

# Valid modes for the self_improve constructor field
SELF_IMPROVE_MODES = ("off", "write", "commit")
