# Decompose Pre-Existing Spec and Plan into Tasks

Decompose the provided specification and plan into a structured JSON task list.

## Inputs Available

- **spec**: Feature specification (markdown)
- **plan**: Technical implementation plan (markdown)
- **agents_registry**: JSON array of available agents (may be empty `[]`)
- **model_family**: Model provider family (claude, gemini, or openai)
- **model_table**: Complexity-to-model-ID mapping for the selected family
- **include_tests**: Whether to generate test tasks (`true` or `false`)
- **include_review**: Whether to generate review tasks (`true` or `false`)
- **create_pr**: Whether to generate PR branch names on phases (`true` or `false`)
- **source**: Project source directory

## Approach

1. **Read the spec** — extract user stories with priorities, functional requirements, acceptance criteria
2. **Read the plan** — extract architecture decisions, file structure, dependencies, complexity estimates
3. **Explore the codebase** using `glob` and `grep` to validate the plan's file paths and understand existing patterns
4. **Decompose** into ordered, dependency-aware tasks

**Task ordering follows the implement → test → review pipeline:**

1. **Implementation tasks** (`entrypoint: "assist"`): The core coding work
2. **Test tasks** (`entrypoint: "write_tests"`): Generated only when `include_tests` is `true`. Each test task covers one or more implementation tasks from the same phase, depends on them, and uses the same agent (if it has `write_tests` capability)
3. **Review tasks** (`entrypoint: "review"`): Generated only when `include_review` is `true`. One review task per phase, depends on all implementation (and test) tasks in that phase, uses the same agent (if it has `review` capability)

Each task gets a sequential `order` value (integer starting at 1) that defines the global execution order for GitHub Actions chaining. Tasks with the same `order` value can run in parallel.

## Agent Assignment Rules

When the `agents_registry` is provided (non-empty JSON array), match tasks to agents based on:

1. **Language/framework match**: Pick the agent whose specialization matches the task's tech stack
2. **Capability match**: Ensure the agent supports the required entrypoint (assist, write_tests, build, etc.)
3. **Fallback**: If no agent matches, use `"unassigned"` with a note

Each agent in the registry:
```json
{
  "name": "monty",
  "source": "github.com/telchak/daggerverse/monty",
  "specialization": "Python backend development",
  "capabilities": ["assist", "review", "write_tests", "build", "upgrade"]
}
```

If `agents_registry` is `[]`, set `suggested_agent` to `null` on all tasks.

**For test tasks**: Use the `write_tests` entrypoint. Only assign an agent if it has `write_tests` in its capabilities.
**For review tasks**: Use the `review` entrypoint. Only assign an agent if it has `review` in its capabilities.

## Model Assignment Rules

Use the **model_table** input to map task complexity to a concrete model ID. The table is provided by the caller based on their chosen **model_family**.

**Complexity guidelines:**
- **low**: Config changes, dependency installs, boilerplate, single-file edits — small context window
- **medium**: Single feature implementation, clear scope, standard patterns — moderate context window
- **high**: Cross-cutting concerns, architecture changes, complex multi-file logic — large context window

**For test tasks**: Use one level above the implementation task's complexity (low→medium, medium→high, high→high).
**For review tasks**: Always use `medium` complexity.

Use the exact model IDs from `model_table` in the `suggested_model` field of each task.

## Output Format

Write a valid JSON object to the `result` output. The JSON must conform exactly to this schema:

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
      "description": "Detailed description specific enough for an LLM to execute",
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
        "reason": "Python backend task"
      },
      "parallel": false,
      "depends_on": [],
      "story_label": null,
      "task_type": "implementation",
      "files_to_modify": ["requirements.txt"],
      "context_needed": ["existing dependency management approach"]
    }
  ],
  "agent_registry_used": [],
  "execution_plan": {
    "phases": [
      {
        "phase": 1,
        "name": "Setup",
        "tasks": ["T001"],
        "parallel": false,
        "pr_branch": "speck/short-feature-name/phase-1-setup"
      }
    ],
    "total_phases": 1,
    "critical_path": ["T001"],
    "parallelizable_groups": []
  }
}
```

### Task Type Values

- `"implementation"`: Core coding work (entrypoint: `assist`)
- `"test"`: Test writing (entrypoint: `write_tests`) — only when `include_tests` is `true`
- `"review"`: Code review (entrypoint: `review`) — only when `include_review` is `true`

### Order Field

The `order` field is a positive integer defining the global execution sequence:
- Tasks with the same `order` value can run in parallel
- Higher `order` values run after lower ones complete
- Within a phase: implementation tasks get the lowest order, then test tasks, then review tasks
- Across phases: phase N's tasks always have higher order than phase N-1's tasks

### PR Branch Field (Phase Level)

When `create_pr` is `true`, each **phase** in `execution_plan.phases` gets a `pr_branch` field. When `create_pr` is `false`, set `pr_branch` to `null` on all phases.

**Branch naming:** `speck/<feature>/phase-<N>-<slug>`

Within each phase, tasks are chained sequentially — each agent's output becomes the next agent's input — and one PR is created per phase from the accumulated changes.

## Rules

- Output MUST be valid JSON — no markdown fences, no prose before or after
- Every task must have a clear, actionable `description`
- `definition_of_done` must contain concrete, verifiable conditions
- `files_to_modify` should reference actual paths from the plan and codebase
- `depends_on` must reference task IDs that appear earlier in the list
- `parallel` is `true` only if the task can run concurrently with others in the same phase
- Phases execute sequentially; tasks within a phase may be parallel
- `suggested_agent` is `null` when no agent registry is provided
- `story_label` uses "US1", "US2" etc. for user story tasks; `null` for setup/foundational
- `order` is a positive integer — tasks sharing an order value are parallelizable
- `task_type` must be one of: `"implementation"`, `"test"`, `"review"`
- Test tasks should reference the implementation tasks they cover in `depends_on` and mention which files/functions to test
- Review tasks should reference all tasks in the phase in `depends_on` and mention what to look for
- If `include_tests` is `false`, do NOT generate any tasks with `task_type: "test"`
- If `include_review` is `false`, do NOT generate any tasks with `task_type: "review"`
- Each phase's `pr_branch` must be `null` when `create_pr` is `false`
- Each phase's `pr_branch` must be a valid Git branch name (lowercase, kebab-case, no spaces) when `create_pr` is `true`
- Each phase must have a unique `pr_branch` value
