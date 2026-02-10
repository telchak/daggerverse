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
