# Test Writing Task

Generate tests for Python modules, classes, functions, or API endpoints.

## Inputs Available

- **source**: Python project source directory
- **target** (optional): Specific file or module to write tests for
- **test_framework** (optional): Preferred test framework (pytest, unittest)

## Approach

1. **Detect test setup**: Use `glob` to find existing test files (`test_*.py`, `*_test.py`, `tests/`) and config files (`pyproject.toml`, `pytest.ini`, `setup.cfg`, `tox.ini`, `conftest.py`)
2. **Follow existing patterns**: Read existing test files to match the project's testing conventions
3. **Identify targets**: If no target is specified, find modules/functions that lack tests
4. **Generate tests**: Write test files using `write_file`

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
