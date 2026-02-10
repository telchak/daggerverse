# Angie

AI-powered Angular development agent with Angular CLI MCP integration. Assists with coding, code review, test generation, builds, and version upgrades — all running inside Dagger containers.

## Installation

```shell
dagger install github.com/certainty-labs/daggerverse/angie@<version>
```

## Features

- **Coding assistant**: Implement features, refactor code, answer questions about your Angular project
- **Code review**: Analyze code for Angular best practices, performance, accessibility, and type safety
- **Test generation**: Generate unit, integration, and e2e tests following Angular testing patterns
- **Build diagnostics**: Build the project, diagnose compilation errors, and suggest fixes
- **Version upgrades**: Detect current version, research breaking changes, and apply migration code changes
- **Angular CLI MCP**: Real-time access to Angular documentation, best practices, and modernize tools
- **Workspace tools**: Read, edit, write, glob, and grep files in your project
- **Per-repo context**: Reads `ANGIE.md`, `AGENT.md`, or `CLAUDE.md` for project-specific instructions

## Functions

| Function | Description |
|----------|-------------|
| `assist` | General Angular coding assistant — implements features, refactors, answers questions |
| `review` | Code review for best practices, performance, accessibility, type safety |
| `write-tests` | Generate unit/integration/e2e tests for components and services |
| `build` | Build, compile, or lint the project — diagnoses errors and suggests fixes |
| `upgrade` | Upgrade Angular version — detects current version, applies breaking changes |
| `develop-github-issue` | Read a GitHub issue, implement it, create a PR, and comment on the issue |

## Quick Start

### Coding Assistant

```shell
dagger call assist \
  --source=. \
  --assignment="Add a login component with reactive forms and validation"
```

### Code Review

```shell
# Review the entire project
dagger call review --source=.

# Review with a specific focus
dagger call review \
  --source=. \
  --focus="performance and change detection strategy"

# Review a diff
dagger call review \
  --source=. \
  --diff="$(git diff main..feature-branch)"
```

### Test Generation

```shell
# Generate tests for the whole project
dagger call write-tests --source=.

# Generate tests for a specific component
dagger call write-tests \
  --source=. \
  --target="src/app/auth/login.component.ts"

# Specify test framework
dagger call write-tests \
  --source=. \
  --target="src/app/services/auth.service.ts" \
  --test-framework="jest"
```

### Build Diagnostics

```shell
# Analyze build configuration and fix issues
dagger call build --source=.

# Run a specific build command
dagger call build \
  --source=. \
  --command="ng build --configuration production"
```

### Version Upgrade

```shell
# Upgrade to Angular 19
dagger call upgrade \
  --source=. \
  --target-version="19"

# Dry run — analyze without modifying files
dagger call upgrade \
  --source=. \
  --target-version="19" \
  --dry-run
```

## GitHub Integration

The `develop-github-issue` function enables a full issue-to-PR workflow: read a GitHub issue, implement the changes with the `assist` agent, create a Pull Request, and comment on the issue with a summary — all in one step.

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--github-token` | GitHub token (as a Dagger secret) with `repo` and `pull-requests` permissions | Yes |
| `--issue-id` | GitHub issue number | Yes |
| `--repository` | GitHub repository URL (e.g. `https://github.com/owner/repo`) | Yes |
| `--source` | Angular project source directory | No (uses constructor source) |
| `--base` | Base branch for the PR | No (defaults to `main`) |

### CLI Usage

```shell
dagger call develop-github-issue \
  --github-token=env:GITHUB_TOKEN \
  --issue-id=42 \
  --repository="https://github.com/owner/my-angular-app" \
  --source=.
```

### GitHub Actions Workflow

Create `.github/workflows/develop.yml` in your repository:

```yaml
name: Angie — Develop Issue

on:
  issues:
    types: [labeled]

jobs:
  develop:
    if: github.event.label.name == 'angie'
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
          module: github.com/certainty-labs/daggerverse/angie
          args: >-
            develop-github-issue
            --github-token=env:GITHUB_TOKEN
            --issue-id=${{ github.event.issue.number }}
            --repository="${{ github.server_url }}/${{ github.repository }}"
            --source=.
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          # Optional: DAGGER_CLOUD_TOKEN: ${{ secrets.DAGGER_CLOUD_TOKEN }}
```

### Setup

1. **Enable PR creation in Actions**: Go to repository Settings → Actions → General → Workflow permissions → select "Read and write permissions" and check "Allow GitHub Actions to create and approve pull requests"
2. **Add LLM API key**: Go to Settings → Secrets and variables → Actions → add your LLM provider key (e.g. `ANTHROPIC_API_KEY`)
3. **Label an issue**: Add the `angie` label to any issue — the workflow will trigger, implement the changes, and open a PR

## Constructor Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Angular project source directory | (required) |
| `--node-version` | Node.js version for the Angular CLI MCP server | `22` |

## ANGIE.md

Create an `ANGIE.md` file in your project root to give the agent project-specific context:

```markdown
# Project Context

## Framework
- Angular 18 with standalone components
- Angular Material for UI
- NgRx for state management

## Conventions
- Use signals for local component state
- Use inject() instead of constructor injection
- Use new control flow syntax (@if, @for, @switch)
- Tests use Jest with Angular Testing Library

## Build
- Build command: `npm run build:prod`
- Output directory: dist/my-app
```

The agent also recognizes `AGENT.md` and `CLAUDE.md` as fallbacks.

## Angular CLI MCP Integration

Angie uses the [Angular CLI MCP server](https://angular.dev/tools/cli/mcp) to access:

- Angular documentation and API references
- Best practices and coding patterns
- Build and test capabilities
- E2E testing tools
- Modernize/migration tools

The MCP server runs as a Dagger service container (`node:<version>` with `npx -y @angular/cli mcp`), so no local Node.js installation is required.

## Testing

Tests are located in `daggerverse/tests/` and run all 5 agent entrypoints against the [RealWorld Angular example app](https://github.com/realworld-apps/angular-realworld-example-app) (Angular 21, standalone components, vitest, playwright).

```shell
# Run with default RealWorld app (cloned automatically)
dagger call -m ./daggerverse/tests angie

# Run against your own Angular project
dagger call -m ./daggerverse/tests angie --source=./my-angular-app
```

The test suite covers:
- **assist** — project architecture analysis
- **review** — best practices review (standalone components, signals)
- **write-tests** — vitest test generation for `app.component.ts`
- **build** — build configuration analysis
- **upgrade** — dry-run version upgrade analysis

## LLM Configuration

This module uses the Dagger LLM API. Configure your preferred provider:

| Provider | Required Env Var | Model Env Var |
|----------|------------------|---------------|
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` |

## License

Apache 2.0
