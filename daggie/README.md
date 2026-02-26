# Daggie

AI-powered Dagger CI specialist agent for creating, explaining, and debugging Dagger modules and pipelines. Runs inside Dagger containers with live schema introspection via the Dagger MCP server.

## Installation

```shell
dagger install github.com/certainty-labs/daggerverse/daggie@<version>
```

## Features

- **Coding assistant**: Create Dagger pipelines and modules across all SDKs (Python, TypeScript, Go)
- **Explain concepts**: Answer questions about Dagger modules, CLI commands, and pipeline patterns
- **Debug pipelines**: Diagnose pipeline errors and apply fixes to source code
- **Code review**: Review Dagger modules for best practices, caching, and correctness
- **Module references**: Clone and read existing Dagger modules at runtime for learning patterns
- **Dagger MCP**: Live access to Dagger engine schema introspection, GraphQL queries, and SDK guidance
- **Workspace tools**: Read, edit, write, glob, and grep files in your project
- **Per-repo context**: Reads `DAGGIE.md`, `DAGGER.md`, `AGENT.md`, or `CLAUDE.md` for project-specific instructions

## Functions

| Function | Description |
|----------|-------------|
| `assist` | Create Dagger pipelines and modules, implement features |
| `explain` | Explain Dagger modules, CLI commands, pipeline patterns, and concepts |
| `debug` | Diagnose and fix Dagger pipeline errors from error output |
| `review` | Review Dagger module code for quality, best practices, and correctness |
| `read-module` | Read a Dagger module from a Git repository for reference |
| `develop-github-issue` | Read a GitHub issue, route to the best agent, create a PR |
| `suggest-github-fix` | Analyze a CI failure and post inline code suggestions on a GitHub PR |

## Quick Start

### Coding Assistant

```shell
dagger call assist \
  --source=. \
  --assignment="Create a Dagger module for building and testing this Python project"
```

### With Reference Modules

You can pass existing Dagger modules as references so the agent can read their
source code and learn from their patterns before writing yours.

The `--module-urls` flag accepts Git URLs in the format:
`https://github.com/<owner>/<repo>.git#<branch>:<path-to-module>`

```shell
# Use kpenfound's Go and Nginx modules as references to build your own.
# Daggie will clone these modules, read their source code, and follow
# the same patterns (caching, multi-stage builds, service bindings)
# when creating your module.
dagger call assist \
  --source=. \
  --module-urls="https://github.com/kpenfound/dagger-modules.git#main:golang,https://github.com/kpenfound/dagger-modules.git#main:nginx" \
  --assignment="Create a Dagger module (Go SDK) for building and serving my Go web app with Nginx as a reverse proxy. Follow the patterns from the reference modules."
```

You can also mix references from different repositories:

```shell
# Combine a reference from kpenfound's repo (Postgres service module)
# with one from our own daggerverse (Python build patterns)
dagger call assist \
  --source=. \
  --module-urls="https://github.com/kpenfound/dagger-modules.git#main:postgres,https://github.com/certainty-labs/daggerverse.git#main:daggerverse/python-build" \
  --assignment="Create a Dagger module that builds my Python API and runs integration tests against a Postgres service"
```

### Explain a Concept

```shell
dagger call explain \
  --question="What is a Dagger module and how does dagger.json configure it?"
```

### Debug a Pipeline Error

```shell
dagger call debug \
  --source=. \
  --error-output="$(dagger call build 2>&1)"
```

### Code Review

```shell
# Review the entire module
dagger call review --source=.

# Review with a specific focus
dagger call review \
  --source=. \
  --focus="caching strategy and container optimization"

# Review a diff
dagger call review \
  --source=. \
  --diff="$(git diff main..feature-branch)"
```

## GitHub Integration

The `develop-github-issue` function enables a full issue-to-PR workflow: read a GitHub issue, automatically select the best agent function (`assist`, `explain`, or `debug`) based on the issue content, implement the changes, create a Pull Request, and comment on the issue with a summary.

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--github-token` | GitHub token (as a Dagger secret) with `repo` and `pull-requests` permissions | Yes |
| `--issue-id` | GitHub issue number | Yes |
| `--repository` | GitHub repository URL (e.g. `https://github.com/owner/repo`) | Yes |
| `--source` | Project source directory | No (uses constructor source) |
| `--base` | Base branch for the PR | No (defaults to `main`) |

### CLI Usage

```shell
dagger call develop-github-issue \
  --github-token=env:GITHUB_TOKEN \
  --issue-id=42 \
  --repository="https://github.com/owner/my-dagger-project" \
  --source=.
```

### GitHub Actions Workflow

Create `.github/workflows/develop.yml` in your repository:

```yaml
name: Daggie — Develop Issue

on:
  issues:
    types: [labeled]

jobs:
  develop:
    if: github.event.label.name == 'daggie'
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
          module: github.com/certainty-labs/daggerverse/daggie
          args: >-
            develop-github-issue
            --github-token=env:GITHUB_TOKEN
            --issue-id=${{ github.event.issue.number }}
            --repository="${{ github.server_url }}/${{ github.repository }}"
            --source=.
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

## Suggest Fix on CI Failure

The `suggest-github-fix` function analyzes CI pipeline failures and posts GitHub "suggested changes" directly on the PR. Developers can then apply the fixes with one click from the GitHub UI.

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--github-token` | GitHub token (as a Dagger secret) with `repo` and `pull-requests` permissions | Yes |
| `--pr-number` | Pull request number | Yes |
| `--repo` | GitHub repository URL (e.g. `https://github.com/owner/repo`) | Yes |
| `--commit-sha` | HEAD commit SHA of the PR branch | Yes |
| `--error-output` | CI error output (stderr/stdout) | Yes |
| `--source` | Project source directory | No (uses constructor source) |

### CLI Usage

```shell
dagger call suggest-github-fix \
  --github-token=env:GITHUB_TOKEN \
  --pr-number=123 \
  --repo="https://github.com/owner/my-dagger-project" \
  --commit-sha="abc123" \
  --error-output="$(cat ci-output.log)" \
  --source=.
```

### GitHub Actions Workflow

Create `.github/workflows/suggest-fix.yml` to automatically call Daggie when a CI step fails on a pull request:

```yaml
name: Daggie — Suggest Fix on CI Failure

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ci:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      # Your normal CI steps — build, lint, test, etc.
      - name: Build and test
        id: ci
        continue-on-error: true    # Don't fail the job yet — let Daggie analyze first
        run: |
          # Run your CI pipeline and capture the output
          dagger call build --source=. 2>&1 | tee ci-output.log

      # If CI failed, ask Daggie to analyze the error and suggest fixes
      - name: Suggest fix with Daggie
        if: steps.ci.outcome == 'failure'
        uses: dagger/dagger-for-github@v7
        with:
          verb: call
          version: "latest"
          module: github.com/certainty-labs/daggerverse/daggie
          args: >-
            suggest-github-fix
            --github-token=env:GITHUB_TOKEN
            --pr-number=${{ github.event.pull_request.number }}
            --repo="${{ github.server_url }}/${{ github.repository }}"
            --commit-sha=${{ github.event.pull_request.head.sha }}
            --error-output="$(cat ci-output.log)"
            --source=.
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

      # Fail the job if CI failed (after Daggie has posted suggestions)
      - name: Fail if CI failed
        if: steps.ci.outcome == 'failure'
        run: exit 1
```

The workflow:
1. Runs your normal CI steps with `continue-on-error: true` and captures output to a log file
2. If CI fails, Daggie reads the error output, analyzes the source code, and posts inline "suggested changes" on the PR
3. The job still fails at the end so the PR shows a red check — but developers get actionable fix suggestions they can apply with one click

## Constructor Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Project source directory | `/` |
| `--module-urls` | Git URLs of Dagger modules to clone for reference | `[]` |
| `--self-improve` | Self-improvement mode: `off`, `write`, or `commit` | `off` |

## Self-Improvement

Pass `--self-improve` to let the agent update your context file with discoveries as it works.

| Mode | Behavior |
|------|----------|
| `off` (default) | No change to current behavior |
| `write` | Agent updates the context file (e.g. `DAGGIE.md`) in the returned directory |
| `commit` | Agent updates the context file and creates a git commit in the returned directory |

```shell
dagger call assist \
  --source=. \
  --self-improve=write \
  --assignment="Create a Dagger pipeline for building and testing this Python project"
```

The agent appends learned context (architecture patterns, gotchas, conventions) under a `## Learned Context` heading. Existing content is never overwritten. Applies to `assist` and `debug` (entrypoints that return a directory).

## DAGGIE.md

Create a `DAGGIE.md` file in your project root to give the agent project-specific context:

```markdown
# Project Context

## Module Structure
- Python SDK module with async functions
- Uses dagger.json dependencies for shared modules

## Conventions
- Cache pip dependencies with dag.cache_volume("pip-cache")
- Use multi-stage builds for smaller images
- Always pin base image versions

## Build
- Entry point: `dagger call build --source=.`
- Test: `dagger call test --source=.`
```

The agent also recognizes `DAGGER.md`, `AGENT.md`, and `CLAUDE.md` as fallbacks.

## Dagger MCP Integration

Daggie uses the [dagger-mcp](../dagger-mcp/) module to access the Dagger engine at runtime:

- **learn_schema** — introspect any type from the Dagger GraphQL API
- **run_query** — execute GraphQL queries against the live engine
- **learn_sdk** — get SDK translation guidance (Python, TypeScript, Go)
- **dagger_version** — check the running engine version

MCP is enabled for `assist`, `explain`, and `debug` tasks. The `review` task uses workspace tools only.

## Testing

Tests are located in `daggerverse/tests/` and run all agent entrypoints.

```shell
# Run all Daggie tests
dagger call -m ./daggerverse/tests daggie

# Run individual tests
dagger call -m ./daggerverse/tests daggie-assist
dagger call -m ./daggerverse/tests daggie-explain
dagger call -m ./daggerverse/tests daggie-debug
```

The test suite covers:
- **assist** — create a Dagger pipeline for a Python web app
- **explain** — answer questions about Dagger modules and dagger.json
- **debug** — fix a broken dagger.json (missing engineVersion)

## LLM Configuration

This module uses the Dagger LLM API. Configure your preferred provider:

| Provider | Required Env Var | Model Env Var |
|----------|------------------|---------------|
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` |

## License

Apache 2.0
