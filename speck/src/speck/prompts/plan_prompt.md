# Technical Implementation Plan Task

Generate a technical implementation plan from the **spec** input.

## Inputs Available

- **spec**: Feature specification (markdown, output of the specify step)
- **tech_stack** (optional): Tech stack preferences from the user
- **source**: Project source directory (explore it to understand existing architecture)

## Approach

1. **Explore** the workspace to understand: existing tech stack, project structure, build tools, test framework, dependencies
2. **Read the specification** carefully — extract all user stories, requirements, and success criteria
3. **Generate the plan** following the structure below

## Plan Structure

### Technical Context
- Current tech stack (discovered from codebase)
- Frameworks and libraries in use
- Build and test tooling
- Deployment patterns (if discoverable)

### Architecture Decision Records
For each significant decision:
```
**ADR-n: [Decision Title]**
- Context: [Why this decision is needed]
- Decision: [What was chosen]
- Rationale: [Why chosen over alternatives]
- Alternatives: [What else was considered]
```

### Project Structure
Show the file/directory structure for the new feature:
```
src/
  feature/
    models.py       — Data models for [entities]
    service.py      — Business logic for [operations]
    routes.py       — API endpoints (if applicable)
tests/
  test_feature/
    test_models.py
    test_service.py
```

### Dependencies
List new dependencies needed:
- `package-name` — purpose, version constraint

### Complexity Analysis
For each user story, estimate:
- **Low**: Config, boilerplate, single-file changes
- **Medium**: Multi-file feature, standard patterns, clear scope
- **High**: Cross-cutting concerns, complex logic, architecture changes

### Risk Assessment
- What could go wrong?
- What are the unknowns?
- What needs research before implementation?

## Rules

- Ground the plan in the actual codebase — reference existing files, patterns, and conventions
- Respect existing architecture — don't propose rewrites unless the spec demands it
- Be specific about file paths and module boundaries
- If `tech_stack` is provided, use those preferences; otherwise infer from the codebase

## Output

Write the full plan to the `result` output as markdown.
