# Test Writing Task

**YOUR #1 JOB: Call `writeFile` to create test files.** If you finish without calling `writeFile` at least once, the task has FAILED and your work is lost. Do not just analyze or describe tests — you must write them to disk.

## Steps

1. Read the target file to understand what needs testing
2. Check for existing test files and config (`glob` for `*.spec.ts`, `vitest.config.*`, `jest.config.*`) to match conventions
3. **Call `writeFile` to create the test file(s)** — this is the critical step

Do NOT skip step 3. Do NOT end your turn without having called `writeFile`.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **workspace**: the project source, which the workspace tools read and edit
- **target** (optional): Specific file or component to write tests for
- **test_framework** (optional): Preferred test framework (jest, karma, vitest)

## Test Patterns

- **Components**: TestBed, component creation, input/output bindings, template rendering
- **Services**: method return values, HttpTestingController for HTTP, observable streams
- **Directives**: host element behavior, structural rendering

## Reminder

You MUST call `writeFile` to create test files. This is not optional.
