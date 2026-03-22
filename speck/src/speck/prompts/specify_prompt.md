# Feature Specification Task

Generate a structured feature specification from the **feature_description** input.

## Inputs Available

- **feature_description**: Natural language description of what to build (may come from a prompt or a GitHub issue)
- **source**: Project source directory (explore it to understand existing code and patterns)

## Approach

1. **Explore** the workspace using `glob` and `grep` to understand the existing codebase — project structure, frameworks, conventions, existing features
2. **Extract key concepts** from the feature description: actors, actions, data, constraints
3. **Generate the specification** following the structure below

## Specification Structure

Produce a complete specification with these sections:

### Feature Overview
- Feature name (concise, 2-4 words)
- One-paragraph summary of what and why

### User Stories
For each user story, assign a priority (P1, P2, P3):

```
**[USn] Story Title** (Priority: Pn)
As a [actor], I want to [action], so that [benefit].

Acceptance Scenarios:
- Given [context], When [action], Then [expected outcome]
- Given [context], When [action], Then [expected outcome]
```

### Functional Requirements
Numbered, testable requirements derived from the user stories:
- FR1: The system shall...
- FR2: The system shall...

### Edge Cases & Error Handling
- What happens when inputs are invalid?
- What are the boundary conditions?
- What error messages should users see?

### Success Criteria
Measurable, technology-agnostic outcomes:
- Users can complete [task] in under [time]
- System supports [N] concurrent [operations]

### Assumptions
Document any reasonable defaults you chose when the description was ambiguous.

### Out of Scope
Explicitly list what this feature does NOT cover.

## Rules

- Focus on **WHAT** and **WHY**, never **HOW** (no tech stack, APIs, code structure)
- Written for business stakeholders, not developers
- Every requirement must be testable and unambiguous
- Maximum 3 clarification markers `[NEEDS CLARIFICATION: ...]` — prefer reasonable defaults
- Make informed guesses based on codebase context and industry standards
- Prioritize: scope > security/privacy > user experience > technical details

## Output

Write the full specification to the `result` output as markdown.
