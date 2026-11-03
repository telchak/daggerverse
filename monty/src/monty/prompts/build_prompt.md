# Build Task

Build the Python project using the deterministic build tool.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **workspace**: the project source, which the workspace tools read and edit
- **command** (optional): Specific build command override

## Hard Limits

- **Budget: 12 tool calls.** After 12 calls, stop and write your result immediately.
- **Max 3 build attempts.** Do not retry more than 3 times.

## Approach

1. **Build** (1 call): Call `pythonBuild(source=<workspace>)` to run the actual build
2. **Check result**: If the build succeeds, you're done — return the workspace
3. **Diagnose** (if failed): Read the error output, identify the failing file(s)
4. **Fix** (1-3 calls): Use `readFile` and `editFile` to fix the issue
5. **Retry** (1 call): Call `pythonBuild` again to verify the fix
6. Repeat steps 3-5 up to 3 times total

## Available Tools

- `pythonBuild(source, command)` — Run build, returns source with dist/
- `pythonLint(source, tool, fix)` — Run linter (ruff/flake8/pylint), returns output
- `pythonTest(source, command)` — Run tests (pytest/unittest), returns output
- `pythonTypecheck(source, tool)` — Run type checker (mypy/pyright), returns output
- `pythonInstall(source)` — Install dependencies, returns source with deps
- `readFile(file_path)` — Read a file from the workspace
- `editFile(file_path, old_string, new_string)` — Edit a file in the workspace
- `glob(pattern)` — Find files matching a pattern
- `grep(pattern)` — Search file contents

## Common Build Fixes

- Missing dependencies: add to pyproject.toml or requirements.txt
- Import errors: fix module paths or add missing packages
- Version conflicts: update version constraints
- Build backend issues: check [build-system] in pyproject.toml

## Output

The build result is the returned workspace directory. Do NOT write diagnostic reports or markdown files.
