# Full Pipeline: Specify -> Plan -> Decompose

Run the complete spec-driven development pipeline and produce a structured JSON task list.

## Inputs Available

- **feature_description**: Natural language description of what to build
- **agents_registry**: JSON array of available agents (may be empty `[]`)
- **tech_stack** (optional): Tech stack preferences
- **model_family**: Model provider family (claude, gemini, or openai)
- **model_table**: Complexity-to-model-ID mapping for the selected family
- **include_tests**: Whether to generate test tasks (`true` or `false`)
- **include_review**: Whether to generate review tasks (`true` or `false`)
- **create_pr**: Whether to generate PR branch names on phases (`true` or `false`)
- **source**: Project source directory

## Pipeline Steps

### Step 1: Explore the Codebase

Use `glob` and `grep` to understand:
- Project structure (languages, frameworks, build tools)
- Existing patterns and conventions
- Test framework in use
- Key entry points and models

### Step 2: Generate Specification

From the feature description, mentally generate a specification with:
- User stories with priorities (P1, P2, P3)
- Functional requirements
- Acceptance criteria
- Success criteria

### Step 3: Generate Plan

From the specification and codebase exploration, mentally generate a plan with:
- Architecture decisions
- File structure for the new feature
- Dependencies needed
- Complexity per user story

### Step 4: Decompose into Tasks

Break the plan into an ordered, dependency-aware task list. Each task maps to a single unit of work that one coding agent can complete.

**Task ordering follows the implement → test → review pipeline:**

1. **Implementation tasks** (`entrypoint: "assist"`): The core coding work
2. **Test tasks** (`entrypoint: "write-tests"`): Generated only when `include_tests` is `true`. Each test task covers one or more implementation tasks from the same phase, depends on them, and uses the same agent (if it has `write-tests` capability)
3. **Review tasks** (`entrypoint: "review"`): Generated only when `include_review` is `true`. One review task per phase, depends on all implementation (and test) tasks in that phase, uses the same agent (if it has `review` capability)

Each task gets a sequential `order` value (integer starting at 1) that defines the global execution order for GitHub Actions chaining. Tasks with the same `order` value can run in parallel.

## Agent Assignment Rules

When the `agents_registry` is provided (non-empty JSON array), match tasks to agents based on:

1. **Language/framework match**: Pick the agent whose specialization matches the task's tech stack
2. **Capability match**: Ensure the agent supports the required entrypoint (assist, write-tests, build, etc.)
3. **Fallback**: If no agent matches, use `"unassigned"` with a note explaining what's needed

Each agent in the registry has this shape:
```json
{
  "name": "monty",
  "source": "github.com/telchak/daggerverse/monty",
  "specialization": "Python backend development",
  "capabilities": ["assist", "review", "write-tests", "build", "upgrade"]
}
```

If `agents_registry` is `[]`, set `suggested_agent` to `null` on all tasks.

**For test tasks**: Use the `write-tests` entrypoint. Only assign an agent if it has `write-tests` in its capabilities.
**For review tasks**: Use the `review` entrypoint. Only assign an agent if it has `review` in its capabilities.

## Model Assignment Rules

Use the **model_table** input to map task complexity to a concrete model ID. The table is provided by the caller based on their chosen **model_family**.

**Complexity guidelines:**
- **low**: Config changes, dependency installs, boilerplate, single-file edits — small context window
- **medium**: Single feature implementation, clear scope, standard patterns — moderate context window
- **high**: Cross-cutting concerns, architecture changes, complex multi-file logic — large context window

**For test tasks**: Use one level above the implementation task's complexity (low→medium, medium→high, high→high) since tests need to understand the implementation context.
**For review tasks**: Always use `medium` complexity — reviews need to understand the code but don't generate large amounts.

Use the exact model IDs from `model_table` in the `suggested_model` field of each task.

## Output Format

You MUST write a valid JSON object to the `result` output. The JSON must conform exactly to this schema:

```json
{
  "feature": "short-feature-name",
  "spec_summary": "One-line summary of the feature",
  "total_tasks": 6,
  "tasks": [
    {
      "id": "T001",
      "order": 1,
      "phase": 1,
      "phase_name": "Setup",
      "title": "Short task title",
      "description": "Detailed description of what to implement, specific enough for an LLM to execute without additional context",
      "definition_of_done": [
        "Concrete, verifiable condition 1",
        "Concrete, verifiable condition 2"
      ],
      "estimated_complexity": "low",
      "suggested_model": "<model ID from model_table for the estimated_complexity>",
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
      {
        "phase": 1,
        "name": "Setup",
        "tasks": ["T001"],
        "parallel": false,
        "pr_branch": "speck/short-feature-name/phase-1-setup"
      },
      {
        "phase": 2,
        "name": "User Story 1 - Core Feature",
        "tasks": ["T002", "T003"],
        "parallel": true,
        "pr_branch": "speck/short-feature-name/phase-2-core-feature"
      }
    ],
    "total_phases": 3,
    "critical_path": ["T001", "T002", "T004"],
    "parallelizable_groups": [["T002", "T003"], ["T005", "T006"]]
  }
}
```

### Task Type Values

- `"implementation"`: Core coding work (entrypoint: `assist`)
- `"test"`: Test writing (entrypoint: `write-tests`) — only when `include_tests` is `true`
- `"review"`: Code review (entrypoint: `review`) — only when `include_review` is `true`

### Order Field

The `order` field is a positive integer defining the global execution sequence:
- Tasks with the same `order` value can run in parallel
- Higher `order` values run after lower ones complete
- Within a phase: implementation tasks get the lowest order, then test tasks, then review tasks
- Across phases: phase N's tasks always have higher order than phase N-1's tasks

Example ordering with `include_tests=true` and `include_review=true`:
- Phase 1: T001 (implement, order=1), T002 (implement, order=1), T003 (test, order=2), T004 (review, order=3)
- Phase 2: T005 (implement, order=4), T006 (test, order=5), T007 (review, order=6)

### PR Branch Field (Phase Level)

When `create_pr` is `true`, each **phase** in `execution_plan.phases` gets a `pr_branch` field — the Git branch name for a PR containing all the phase's accumulated changes. When `create_pr` is `false`, set `pr_branch` to `null` on all phases.

**Branch naming convention:** `speck/<feature>/phase-<N>-<slug>`
- `<feature>` is the `feature` field value (kebab-case)
- `<N>` is the phase number
- `<slug>` is a kebab-case version of the phase name

Example: `speck/user-auth/phase-1-setup`, `speck/user-auth/phase-2-core-feature`

**Execution model:** The CI workflow matrices by **phase** (not by task). Within each phase, tasks are chained sequentially — each agent's output becomes the next agent's input:
1. Implementation agent runs on the source → returns modified source
2. Test agent runs on modified source → returns source with tests added
3. Review agent runs on source with tests → returns final source
4. One PR is created per phase from the accumulated changes

## Rules

- Output MUST be valid JSON — no markdown fences, no prose before or after
- Every task must have a clear, actionable `description` — an LLM should be able to complete it without asking questions
- `definition_of_done` must contain concrete, verifiable conditions (not vague statements)
- `files_to_modify` should reference actual paths based on your codebase exploration
- `depends_on` must reference task IDs that appear earlier in the list
- `parallel` is `true` only if the task can run concurrently with other tasks in the same phase
- Tasks within the same phase that are marked `parallel: true` can run simultaneously
- Phases execute sequentially; tasks within a phase may be parallel
- `suggested_agent` is `null` when no agent registry is provided
- `story_label` uses the format "US1", "US2", etc. for user story tasks; `null` for setup/foundational tasks
- `order` is a positive integer — tasks sharing an order value are parallelizable
- `task_type` must be one of: `"implementation"`, `"test"`, `"review"`
- Test tasks should reference the implementation tasks they cover in `depends_on` and mention which files/functions to test in the description
- Review tasks should reference all tasks in the phase in `depends_on` and mention what to look for (correctness, security, performance, conventions)
- If `include_tests` is `false`, do NOT generate any tasks with `task_type: "test"`
- If `include_review` is `false`, do NOT generate any tasks with `task_type: "review"`
- Each phase's `pr_branch` must be `null` when `create_pr` is `false`
- Each phase's `pr_branch` must be a valid Git branch name (lowercase, kebab-case, no spaces) when `create_pr` is `true`
- Each phase must have a unique `pr_branch` value
