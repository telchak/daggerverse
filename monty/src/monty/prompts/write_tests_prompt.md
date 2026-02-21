# Test Writing Task

**YOUR #1 JOB: Call `write_file` to create test files.** If you finish without calling `write_file` at least once, the task has FAILED and your work is lost. Do not just analyze or describe tests — you must write them to disk.

## Steps

1. Read the target file to understand what needs testing
2. Check for existing test files and config (`glob` for `test_*.py`, `conftest.py`, `pyproject.toml`) to match conventions
3. **Call `write_file` to create the test file(s)** — this is the critical step

Do NOT skip step 3. Do NOT end your turn without having called `write_file`.

**Budget: 10 tool calls.** Focus on the target file and existing test patterns.

## Inputs Available

- **source**: Python project source directory
- **target** (optional): Specific file or module to write tests for
- **test_framework** (optional): Preferred test framework (pytest, unittest)

## Test Patterns

- **Functions/Modules**: valid inputs, edge cases, error handling, type handling
- **Classes**: init, methods, properties, mock dependencies with `unittest.mock` or `pytest-mock`
- **API endpoints**: HTTP methods, status codes, validation, auth, TestClient/APIClient
- **Async**: `pytest-asyncio`, concurrent operations
- **Fixtures**: `conftest.py`, `tmp_path`, `monkeypatch`

## Reminder

You MUST call `write_file` to create test files. This is not optional.
