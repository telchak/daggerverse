# Test Writing Task

**YOUR #1 JOB: Call `writeFile` to create test files.** If you finish without calling `writeFile` at least once, the task has FAILED and your work is lost. Do not just analyze or describe tests — you must write them to disk.

## Steps

1. Read the target file to understand what needs testing
2. Check for existing test files and config (`glob` for `test_*.py`, `conftest.py`, `pyproject.toml`) to match conventions
3. **Call `writeFile` to create the test file(s)** — this is the critical step

Do NOT skip step 3. Do NOT end your turn without having called `writeFile`.

**Budget: 10 tool calls.** Focus on the target file and existing test patterns.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **workspace**: the project source, which the workspace tools read and edit
- **target** (optional): Specific file or module to write tests for
- **test_framework** (optional): Preferred test framework (pytest, unittest)

## Test Patterns

- **Functions/Modules**: valid inputs, edge cases, error handling, type handling
- **Classes**: init, methods, properties, mock dependencies with `unittest.mock` or `pytest-mock`
- **API endpoints**: HTTP methods, status codes, validation, auth, TestClient/APIClient
- **Async**: `pytest-asyncio`, concurrent operations
- **Fixtures**: `conftest.py`, `tmp_path`, `monkeypatch`

## Reminder

You MUST call `writeFile` to create test files. This is not optional.
