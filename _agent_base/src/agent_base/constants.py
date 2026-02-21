"""Shared constants for Dagger coding agents."""

# Entrypoints blocked on all LLMs to prevent recursion
BLOCKED_ENTRYPOINTS = [
    "assist", "review", "write_tests", "build",
    "upgrade", "develop_github_issue", "suggest_github_fix",
]

# Destructive tools blocked on read-only sub-agents
BLOCKED_DESTRUCTIVE = ["edit_file", "write_file", "suggest_github_pr_code_comment"]

# Build/test tools blocked during write_tests to prevent the LLM from
# running tests instead of just writing them (can hang on missing infra)
BLOCKED_BUILD_TOOLS = [
    "python_build", "python_test", "python_lint", "python_typecheck", "python_install",
    "angular_build", "angular_test", "angular_lint", "angular_install",
]
