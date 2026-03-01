# Monty

AI-powered Python development agent with MCP integration. Assists with coding, code review, test generation, builds, and dependency upgrades — all running inside Dagger containers.

## Installation

```shell
dagger install github.com/telchak/daggerverse/monty@<version>
```

## Features

- **Coding assistant**: Implement features, refactor code, answer questions about your Python project
- **Code review**: Analyze code for Python best practices, performance, security, and type safety
- **Test generation**: Generate unit, integration, and e2e tests following Python testing patterns
- **Build diagnostics**: Build the project, diagnose errors, lint and type-check with MCP tools
- **Dependency upgrades**: Detect current versions, research breaking changes, and apply migration code changes
- **python-lft MCP**: Lint (ruff, flake8, pylint, mypy, bandit), format (black, isort), and test (pytest) via MCP
- **pypi MCP**: Package intelligence — versions, dependencies, compatibility checks, security audits
- **Workspace tools**: Read, edit, write, glob, and grep files in your project
- **Per-repo context**: Reads `MONTY.md` + `AGENTS.md` (falls back to `AGENT.md`/`CLAUDE.md`) for project-specific instructions

## Functions

| Function | Description |
|----------|-------------|
| `assist` | General Python coding assistant — implements features, refactors, answers questions |
| `review` | Code review for best practices, performance, security, type safety |
| `write-tests` | Generate unit/integration/e2e tests for modules and packages |
| `build` | Build, lint, or type-check the project — diagnoses errors and suggests fixes |
| `upgrade` | Upgrade Python dependencies — detects current version, applies breaking changes |
| `develop-github-issue` | Read a GitHub issue, route to the best agent, create a PR, and comment on the issue |
| `suggest-github-fix` | Analyze a CI failure and post inline code suggestions on a GitHub PR |

## Quick Start

### Coding Assistant

```shell
dagger call assist \
  --source=. \
  --assignment="Add a FastAPI endpoint with Pydantic validation for user registration"
```

### Code Review

```shell
# Review the entire project
dagger call review --source=.

# Review with a specific focus
dagger call review \
  --source=. \
  --focus="security and input validation"

# Review a diff
dagger call review \
  --source=. \
  --diff="$(git diff main..feature-branch)"
```

### Test Generation

```shell
# Generate tests for the whole project
dagger call write-tests --source=.

# Generate tests for a specific module
dagger call write-tests \
  --source=. \
  --target="src/app/auth.py"

# Specify test framework
dagger call write-tests \
  --source=. \
  --target="src/app/services/user_service.py" \
  --test-framework="pytest"
```

### Build Diagnostics

```shell
# Analyze build configuration and fix issues
dagger call build --source=.

# Run a specific build command
dagger call build \
  --source=. \
  --command="python -m build"
```

### Dependency Upgrade

```shell
# Upgrade Django to version 5.0
dagger call upgrade \
  --source=. \
  --target-package="django" \
  --target-version="5.0"

# Dry run — analyze without modifying files
dagger call upgrade \
  --source=. \
  --target-package="fastapi" \
  --target-version="latest" \
  --dry-run
```

## GitHub Integration

The `develop-github-issue` function enables a full issue-to-PR workflow: read a GitHub issue, automatically select the best agent function (`assist`, `upgrade`, `build`, or `write-tests`) based on the issue content, implement the changes, create a Pull Request, and comment on the issue with a summary — all in one step.

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--github-token` | GitHub token (as a Dagger secret) with `repo` and `pull-requests` permissions | Yes |
| `--issue-id` | GitHub issue number | Yes |
| `--repository` | GitHub repository URL (e.g. `https://github.com/owner/repo`) | Yes |
| `--source` | Python project source directory | No (uses constructor source) |
| `--base` | Base branch for the PR | No (defaults to `main`) |

### CLI Usage

```shell
dagger call develop-github-issue \
  --github-token=env:GITHUB_TOKEN \
  --issue-id=42 \
  --repository="https://github.com/owner/my-python-app" \
  --source=.
```

### GitHub Actions Workflow

Create `.github/workflows/develop.yml` in your repository:

```yaml
name: Monty — Develop Issue

on:
  issues:
    types: [labeled]

jobs:
  develop:
    if: github.event.label.name == 'monty'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Install Dagger
        uses: dagger/dagger-for-github@v7
        with:
          verb: call
          version: "latest"
          module: github.com/telchak/daggerverse/monty
          args: >-
            develop-github-issue
            --github-token=env:GITHUB_TOKEN
            --issue-id=${{ github.event.issue.number }}
            --repository="${{ github.server_url }}/${{ github.repository }}"
            --source=.
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          # Optional: DAGGER_CLOUD_TOKEN: ${{ secrets.DAGGER_CLOUD_TOKEN }}
```

### Setup

1. **Enable PR creation in Actions**: Go to repository Settings → Actions → General → Workflow permissions → select "Read and write permissions" and check "Allow GitHub Actions to create and approve pull requests"
2. **Add LLM API key**: Go to Settings → Secrets and variables → Actions → add your LLM provider key (e.g. `GEMINI_API_KEY`)
3. **Label an issue**: Add the `monty` label to any issue — the workflow will trigger, implement the changes, and open a PR

## Suggest Fix on CI Failure

The `suggest-github-fix` function analyzes CI pipeline failures and posts GitHub "suggested changes" directly on the PR. Developers can apply fixes with one click.

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--github-token` | GitHub token (as a Dagger secret) with `repo` permissions | Yes |
| `--pr-number` | Pull request number | Yes |
| `--repo` | GitHub repository URL (e.g. `https://github.com/owner/repo`) | Yes |
| `--commit-sha` | HEAD commit SHA of the PR branch | Yes |
| `--error-output` | CI error output (stderr/stdout) | Yes |
| `--source` | Source directory of the PR branch | No |

### CLI Usage

```shell
dagger call suggest-github-fix \
  --github-token=env:GITHUB_TOKEN \
  --pr-number=123 \
  --repo="https://github.com/owner/my-python-app" \
  --commit-sha="abc123" \
  --error-output="$(cat ci-output.log)" \
  --source=.
```

### GitHub Actions Workflow

Add a step to your existing CI workflow that runs on failure:

```yaml
name: CI

on:
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        id: tests
        run: |
          pytest 2>&1 | tee test-output.log
        continue-on-error: true

      - name: Suggest fixes on failure
        if: steps.tests.outcome == 'failure'
        uses: dagger/dagger-for-github@v7
        with:
          verb: call
          version: "latest"
          module: github.com/telchak/daggerverse/monty
          args: >-
            suggest-github-fix
            --github-token=env:GITHUB_TOKEN
            --pr-number=${{ github.event.pull_request.number }}
            --repo="${{ github.server_url }}/${{ github.repository }}"
            --commit-sha=${{ github.event.pull_request.head.sha }}
            --error-output="$(cat test-output.log)"
            --source=.
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

      - name: Fail if tests failed
        if: steps.tests.outcome == 'failure'
        run: exit 1
```

## Constructor Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Python project source directory | (required) |
| `--python-version` | Python version for the MCP server containers | `3.13` |
| `--self-improve` | Self-improvement mode: `off`, `write`, or `commit` | `off` |

## Self-Improvement

Pass `--self-improve` to let the agent update context files with discoveries as it works.

| Mode | Behavior |
|------|----------|
| `off` (default) | No change to current behavior |
| `write` | Agent updates context files in the returned directory |
| `commit` | Agent updates context files and creates a git commit in the returned directory |

```shell
dagger call assist \
  --source=. \
  --self-improve=write \
  --assignment="Add a FastAPI health endpoint"
```

The agent writes to **two** files:
- **`MONTY.md`** — Python-specific patterns, framework conventions, tool gotchas
- **`AGENTS.md`** — project architecture, cross-cutting conventions, team preferences

Existing content is never overwritten. Applies to `assist`, `write-tests`, `build`, and `upgrade` (all entrypoints that return a directory).

## MONTY.md

Create a `MONTY.md` file in your project root to give the agent project-specific context:

```markdown
# Project Context

## Framework
- FastAPI with Pydantic v2
- SQLAlchemy 2.0 with async sessions
- Alembic for migrations

## Conventions
- Use type hints everywhere
- Use Pydantic models for request/response schemas
- Use dependency injection via FastAPI Depends
- Tests use pytest with pytest-asyncio

## Build
- Build command: `python -m build`
- Lint: `ruff check .`
- Type check: `mypy src/`
```

The agent also reads `AGENTS.md` for shared project context (falls back to `AGENT.md` and `CLAUDE.md` for legacy repos).

## MCP Integration

Monty uses two MCP servers:

### python-lft (Lint, Format, Test)

[python-lft-mcp](https://github.com/Agent-Hellboy/python-lft-mcp) provides:
- **Linting**: ruff, flake8, pylint, mypy, bandit, pydocstyle
- **Formatting**: black, ruff, isort, autopep8, yapf
- **Testing**: pytest, nose2, unittest

### pypi-query (Package Intelligence)

[pypi-query-mcp-server](https://github.com/loonghao/pypi-query-mcp-server) provides:
- Package info, versions, and dependencies
- Dependency resolution and compatibility checking
- Download statistics and trending packages
- Security risk auditing

Both MCP servers run as Dagger service containers (`python:<version>-slim`), so no local Python installation is required.

## LLM Configuration

This module uses the Dagger LLM API. Configure your preferred provider:

| Provider | Required Env Var | Model Env Var |
|----------|------------------|---------------|
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` |

## License

Apache 2.0
