# Code Review Task

Review the Angular project source code for quality, best practices, and potential issues.

## Inputs Available

- **source**: Angular project source directory
- **diff** (optional): Git diff or PR diff to focus the review on
- **focus** (optional): Specific area to focus on (e.g. "performance", "accessibility", "security")

## Review Criteria

### Angular Patterns
- Standalone components vs NgModule patterns
- Signal usage and reactivity patterns
- Control flow syntax (@if, @for, @switch)
- Dependency injection patterns (inject() vs constructor)
- Change detection strategy

### TypeScript
- Strict typing, no `any` usage
- Proper use of generics and utility types
- Interface vs type usage consistency

### Performance
- OnPush change detection where appropriate
- Lazy loading of routes and components
- TrackBy functions in iterations
- Unsubscribe patterns / takeUntilDestroyed

### Accessibility
- ARIA attributes on interactive elements
- Keyboard navigation support
- Semantic HTML usage

### Testing
- Test coverage for components and services
- Proper test isolation and mocking
- E2E test coverage for critical paths

## Approach

1. If a **diff** is provided, focus the review on those changes
2. If a **focus** is provided, prioritize that area
3. Otherwise, do a general review of the project structure and key files
4. Use `glob` to find relevant files, `read_file` to examine them
5. Use Angular MCP tools to verify best practices when uncertain

## Output

**CRITICAL**: You MUST set the `result` output with your review. Use the `result` output binding function — do not just produce text. Your review will be lost if you skip this step.

Structure your review as follows:

### Issues (must fix)
- List critical issues that should be fixed

### Suggestions (should consider)
- List improvements that would benefit the codebase

### Positive
- Note good patterns and practices found

### Summary
- Overall assessment and priority recommendations

After writing the review, set it on the `result` output immediately.
