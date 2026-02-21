# Test Writing Task

Generate tests for Python modules, classes, functions, or API endpoints.

## Inputs Available

- **source**: Python project source directory
- **target** (optional): Specific file or module to write tests for
- **test_framework** (optional): Preferred test framework (pytest, unittest)

## Approach

1. **Detect test setup**: Use `glob` to find existing test files and config files (`pyproject.toml`, `conftest.py`)
2. **Read the target**: Read the target file and one existing test file (if any) to match conventions
3. **Generate tests**: Use `write_file` to create test files in the workspace

**CRITICAL**: You MUST use the `write_file` tool to create test files. This is the primary goal of this task. If you do not write files, the task has failed.

**Budget: 10 tool calls.** Focus on the target file and existing test patterns.

## Test Patterns

### Function/Module Tests
- Test return values for valid inputs
- Test edge cases (empty inputs, None, boundary values)
- Test error handling (expected exceptions)
- Test type handling when type hints are present

### Class Tests
- Test initialization and default values
- Test methods and their return values
- Test property getters/setters
- Test inheritance behavior if applicable
- Mock dependencies with `unittest.mock` or `pytest-mock`

### API/Endpoint Tests (FastAPI, Django, Flask)
- Test HTTP methods and status codes
- Test request validation and error responses
- Test authentication and authorization
- Test database operations with test fixtures
- Use framework test clients (TestClient, APIClient)

### Async Tests
- Use `pytest-asyncio` for async function tests
- Test concurrent operations
- Test timeout and cancellation behavior

### Fixtures
- Use `conftest.py` for shared fixtures
- Use `tmp_path` for filesystem tests
- Use `monkeypatch` for environment variables

## Output

Write a summary to the `result` output:
- Test files created
- What each test covers
- Any test dependencies added
