# Build Task

Build the Python project using the deterministic build tool.

## Inputs Available

- **source**: Python project source directory (in your workspace)
- **command** (optional): Specific build command override

## Hard Limits

- **Budget: 12 tool calls.** After 12 calls, stop and write your result immediately.
- **Max 3 build attempts.** Do not retry more than 3 times.

## Approach

1. **Build** (1 call): Call `python_build(source=<workspace>)` to run the actual build
2. **Check result**: If the build succeeds, you're done — return the workspace
3. **Diagnose** (if failed): Read the error output, identify the failing file(s)
4. **Fix** (1-3 calls): Use `read_file` and `edit_file` to fix the issue
5. **Retry** (1 call): Call `python_build` again to verify the fix
6. Repeat steps 3-5 up to 3 times total

## Available Tools

- `python_build(source, command)` — Run build, returns source with dist/
- `python_lint(source, tool, fix)` — Run linter (ruff/flake8/pylint), returns output
- `python_test(source, command)` — Run tests (pytest/unittest), returns output
- `python_typecheck(source, tool)` — Run type checker (mypy/pyright), returns output
- `python_install(source)` — Install dependencies, returns source with deps
- `read_file(file_path)` — Read a file from the workspace
- `edit_file(file_path, old_string, new_string)` — Edit a file in the workspace
- `glob(pattern)` — Find files matching a pattern
- `grep(pattern)` — Search file contents

## Common Build Fixes

- Missing dependencies: add to pyproject.toml or requirements.txt
- Import errors: fix module paths or add missing packages
- Version conflicts: update version constraints
- Build backend issues: check [build-system] in pyproject.toml

## Output

The build result is the returned workspace directory. Do NOT write diagnostic reports or markdown files.
