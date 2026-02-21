# Test Writing Task

Generate tests for Angular components, services, directives, or pipes.

## Inputs Available

- **source**: Angular project source directory
- **target** (optional): Specific file or component to write tests for
- **test_framework** (optional): Preferred test framework (jest, karma, vitest)

## Approach

1. **Detect test setup**: Use `glob` to find existing test files (`*.spec.ts`, `*.test.ts`) and config files (`karma.conf.js`, `jest.config.*`, `vitest.config.*`)
2. **Follow existing patterns**: Read existing test files to match the project's testing conventions
3. **Read the target**: Read the target file to understand what needs to be tested
4. **Generate tests**: Use `write_file` to create test files in the workspace

**CRITICAL**: You MUST use the `write_file` tool to create test files. This is the primary goal of this task. If you do not write files, the task has failed.

## Test Patterns

### Component Tests
- Test component creation and initialization
- Test input/output bindings
- Test template rendering and DOM interactions
- Test lifecycle hooks
- Mock dependencies with `TestBed`

### Service Tests
- Test service methods and return values
- Mock HTTP calls with `HttpTestingController`
- Test error handling
- Test observable streams

### Directive Tests
- Test directive behavior on host elements
- Test structural directive rendering

### E2E Tests (if target mentions e2e)
- Test user flows end-to-end
- Test navigation and routing
- Test form submissions

## Output

Write a summary to the `result` output:
- Test files created
- What each test covers
- Any test dependencies added
