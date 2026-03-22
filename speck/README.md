# Speck

AI-powered spec-driven development agent. Takes a prompt or GitHub issue, generates a specification and technical plan, then decomposes it into structured, agent-assignable tasks — all running inside Dagger containers.

Inspired by [spec-kit](https://github.com/github/spec-kit)'s Spec-Driven Development methodology.

## Installation

```shell
dagger install github.com/telchak/daggerverse/speck@<version>
```

## Features

- **Specification generation**: Produce user stories, acceptance criteria, functional requirements, and success criteria from a prompt or GitHub issue
- **Technical planning**: Generate architecture decisions, project structure, dependency analysis, and complexity estimates grounded in your actual codebase
- **Task decomposition**: Break plans into dependency-ordered, parallelizable tasks with agent and model assignments
- **Agent matching**: Automatically assign tasks to the right coding agent (Monty, Angie, Daggie, etc.) based on language, framework, and capabilities
- **Model suggestions**: Recommend haiku/sonnet/opus per task based on complexity and context window needs
- **GitHub Actions ready**: Structured JSON output designed for `fromJson()` + matrix strategy consumption
- **Workspace tools**: Read, glob, and grep files in your project to ground specs and plans in reality
- **Per-repo context**: Reads `SPECK.md` + `AGENTS.md` (falls back to `AGENT.md`/`CLAUDE.md`) for project-specific instructions

## Functions

| Function | Description |
|----------|-------------|
| `specify` | Generate a feature specification from a prompt or GitHub issue |
| `plan` | Generate a technical implementation plan from a specification |
| `decompose` | Full pipeline (specify → plan → decompose) — returns structured JSON |
| `decompose-from-spec` | Decompose a pre-existing spec and plan into structured JSON tasks |

### Pipeline Options

Both `decompose` and `decompose-from-spec` support these pipeline flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--include-tests` | `false` | Generate test tasks (`write_tests` entrypoint) after implementation tasks |
| `--include-review` | `false` | Generate review tasks (`review` entrypoint) at the end of each phase |
| `--create-pr` | `false` | Add `pr_branch` names to phases for automated PR creation (one PR per phase) |

When enabled, tasks follow the **implement → test → review** pipeline per phase, inspired by [everything-claude-code](https://github.com/affaan-m/everything-claude-code)'s sequential agent chains.

## Quick Start

### Generate a Specification

```shell
dagger call specify \
  --source=. \
  --prompt="Add user authentication with OAuth2 support for Google and GitHub"
```

### Generate a Technical Plan

```shell
dagger call plan \
  --source=. \
  --spec="$(cat spec.md)" \
  --tech-stack="Python, FastAPI, PostgreSQL"
```

### Full Pipeline (Decompose)

```shell
dagger call decompose \
  --source=. \
  --prompt="Add a commenting system for articles" \
  --tech-stack="Python, FastAPI, PostgreSQL" \
  --agents='[
    {
      "name": "monty",
      "source": "github.com/telchak/daggerverse/monty",
      "specialization": "Python backend development",
      "capabilities": ["assist", "review", "write_tests", "build", "upgrade"]
    }
  ]'
```

### Full Pipeline with Tests and Review

```shell
dagger call decompose \
  --source=. \
  --prompt="Add a commenting system for articles" \
  --tech-stack="Python, FastAPI, PostgreSQL" \
  --include-tests \
  --include-review \
  --agents='[
    {
      "name": "monty",
      "source": "github.com/telchak/daggerverse/monty",
      "specialization": "Python backend development",
      "capabilities": ["assist", "review", "write_tests", "build", "upgrade"]
    }
  ]'
```

### Full Pipeline with PR Creation

```shell
dagger call decompose \
  --source=. \
  --prompt="Add a commenting system for articles" \
  --tech-stack="Python, FastAPI, PostgreSQL" \
  --create-pr \
  --include-tests \
  --include-review \
  --agents='[...]'
```

### From a GitHub Issue

```shell
dagger call decompose \
  --source=. \
  --issue-id=42 \
  --repository="https://github.com/owner/repo" \
  --github-token=env:GITHUB_TOKEN \
  --agents='[...]'
```

### From Pre-Existing Spec and Plan

```shell
dagger call decompose-from-spec \
  --source=. \
  --spec="$(cat .specify/specs/my-feature/spec.md)" \
  --plan="$(cat .specify/specs/my-feature/plan.md)" \
  --agents='[...]'
```

## JSON Output Schema

The `decompose` and `decompose-from-spec` functions return a structured JSON object:

```json
{
  "feature": "user-authentication",
  "spec_summary": "Add OAuth2 login with Google and GitHub providers",
  "total_tasks": 6,
  "tasks": [
    {
      "id": "T001",
      "order": 1,
      "phase": 1,
      "phase_name": "Setup",
      "title": "Install OAuth2 dependencies",
      "description": "Detailed, actionable task description...",
      "definition_of_done": [
        "passport.js installed in package.json",
        "Unit test for config loading passes"
      ],
      "estimated_complexity": "low",
      "suggested_model": "claude-haiku-4-5",
      "suggested_agent": {
        "name": "monty",
        "source": "github.com/telchak/daggerverse/monty",
        "entrypoint": "assist",
        "reason": "Python backend task, standard library integration"
      },
      "parallel": false,
      "depends_on": [],
      "story_label": null,
      "task_type": "implementation",
      "files_to_modify": ["requirements.txt", "pyproject.toml"],
      "context_needed": ["existing dependency management approach"]
    }
  ],
  "agent_registry_used": [
    {
      "name": "monty",
      "source": "github.com/telchak/daggerverse/monty",
      "specialization": "Python backend development",
      "tasks_assigned": 4
    }
  ],
  "execution_plan": {
    "phases": [
      {"phase": 1, "name": "Setup", "tasks": ["T001"], "parallel": false, "pr_branch": "speck/user-authentication/phase-1-setup"},
      {"phase": 2, "name": "Core Feature", "tasks": ["T002", "T003"], "parallel": true, "pr_branch": "speck/user-authentication/phase-2-core-feature"}
    ],
    "total_phases": 3,
    "critical_path": ["T001", "T002", "T005"],
    "parallelizable_groups": [["T002", "T003"], ["T004", "T005"]]
  }
}
```

### Task Fields

| Field | Type | Description |
|-------|------|-------------|
| `order` | `int` | Global execution sequence number. Tasks with the same value can run in parallel. |
| `task_type` | `string` | One of `"implementation"`, `"test"`, `"review"` |

### Task Ordering with Pipeline

When `--include-tests` and `--include-review` are enabled, tasks follow this pattern per phase:

```
Phase 1: T001 (implement, order=1) → T002 (test, order=2) → T003 (review, order=3)
Phase 2: T004 (implement, order=4), T005 (implement, order=4) → T006 (test, order=5) → T007 (review, order=6)
```

Use the `order` field in GitHub Actions to chain steps via `needs`/`depends_on` logic.

### PR Creation

When `--create-pr` is enabled, each **phase** in `execution_plan.phases` gets a `pr_branch` field with the Git branch name for a PR containing all the phase's accumulated changes.

**Branch naming:** `speck/<feature>/phase-<N>-<slug>`

**Execution model:** The CI workflow matrices by phase (parallel), then chains tasks sequentially within each phase:
1. Implementation agent runs on the source → returns modified source
2. Test agent runs on modified source → returns source with tests added
3. Review agent runs on final source → returns reviewed source
4. One PR is created per phase from the accumulated changes

When `--create-pr` is not set, `pr_branch` is `null` on all phases.

## Agent Registry

The `--agents` parameter accepts a JSON array of available agents:

```json
[
  {
    "name": "monty",
    "source": "github.com/telchak/daggerverse/monty",
    "specialization": "Python backend development",
    "capabilities": ["assist", "review", "write_tests", "build", "upgrade"]
  },
  {
    "name": "angie",
    "source": "github.com/telchak/daggerverse/angie",
    "specialization": "Angular/TypeScript frontend development",
    "capabilities": ["assist", "review", "write_tests", "build", "upgrade"]
  },
  {
    "name": "daggie",
    "source": "github.com/telchak/daggerverse/daggie",
    "specialization": "Dagger CI module development",
    "capabilities": ["assist", "explain", "debug"]
  },
  {
    "name": "goose",
    "source": "github.com/telchak/daggerverse/goose",
    "specialization": "GCP infrastructure and deployment",
    "capabilities": ["assist", "review", "deploy", "troubleshoot", "upgrade"]
  }
]
```

If no registry is provided, tasks are returned with `"suggested_agent": null`.

## Model Assignment

Tasks are assigned a suggested model based on complexity. Use `--model-family` to select the provider:

```shell
dagger call decompose --source=. --prompt="..." --model-family=gemini
```

| Complexity | Claude (`claude`) | Gemini (`gemini`) | OpenAI (`openai`) |
|-----------|-------------------|-------------------|-------------------|
| Low | `claude-haiku-4-5` | `gemini-3.1-flash-lite-preview` | `gpt-4o-mini` |
| Medium | `claude-sonnet-4-6` | `gemini-3-flash-preview` | `gpt-4o` |
| High | `claude-opus-4-6` | `gemini-3.1-pro-preview` | `o3` |

Default is `claude`. The exact model IDs are embedded in the JSON output's `suggested_model` field for each task.

## GitHub Actions Integration

The JSON output is designed for GitHub Actions matrix strategies. See [`examples/github-actions-workflow.yml`](examples/github-actions-workflow.yml) for a complete workflow that:

1. Triggers when an issue is labeled `speck`
2. Decomposes the issue into phases with tasks via `dagger call decompose`
3. Posts a summary comment on the issue
4. Matrices by phase (parallel), chains tasks sequentially within each phase (impl → test → review)
5. Creates one PR per phase with accumulated changes

```yaml
jobs:
  decompose:
    runs-on: ubuntu-latest
    outputs:
      result: ${{ steps.speck.outputs.result }}
    steps:
      - name: Decompose issue
        id: speck
        run: |
          RESULT=$(dagger call -m github.com/telchak/daggerverse/speck \
            --source=. decompose \
            --issue-id=${{ github.event.issue.number }} \
            --repository="https://github.com/${{ github.repository }}" \
            --github-token=env:GITHUB_TOKEN \
            --create-pr --include-tests --include-review \
            --agents='[...]')
          echo "result=$(echo "$RESULT" | jq -c '.')" >> $GITHUB_OUTPUT

  execute-phase:
    needs: decompose
    strategy:
      matrix:
        phase: ${{ fromJson(needs.decompose.outputs.result).execution_plan.phases }}
    steps:
      - name: Chain tasks sequentially
        run: |
          # Each agent's output becomes the next agent's input
          for task in $(echo '${{ toJson(matrix.phase.tasks) }}' | jq -r '.[]'); do
            dagger call -m "$AGENT_SOURCE" --source=. "$ENTRYPOINT" \
              --assignment="$DESCRIPTION" export --path=.
          done

      - name: Create PR
        run: |
          git checkout -b "${{ matrix.phase.pr_branch }}"
          git add -A && git commit -m "Phase ${{ matrix.phase.phase }}: ${{ matrix.phase.name }}"
          git push origin "${{ matrix.phase.pr_branch }}"
          gh pr create --title "Phase ${{ matrix.phase.phase }}: ${{ matrix.phase.name }}" ...
```

## Constructor Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Project source directory | (required) |

## SPECK.md

Create a `SPECK.md` file in your project root to give the agent project-specific context:

```markdown
# Project Context

## Architecture
- Monorepo with Python backend and Angular frontend
- FastAPI + PostgreSQL backend
- Angular 21 frontend

## Team Conventions
- User stories follow Given/When/Then format
- Tasks should target < 200 lines of change
- Frontend and backend tasks should be parallelizable

## Available Agents
- Monty for all Python work
- Angie for all Angular work
```

The agent also reads `AGENTS.md` for shared project context (falls back to `AGENT.md` and `CLAUDE.md` for legacy repos).

## LLM Configuration

This module uses the Dagger LLM API. Configure your preferred provider:

| Provider | Required Env Var | Model Env Var |
|----------|------------------|---------------|
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` |

## License

Apache 2.0
