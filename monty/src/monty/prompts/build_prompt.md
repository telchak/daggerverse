# Build Task

Build, lint, or type-check the Python project and diagnose any errors.

## Inputs Available

- **source**: Python project source directory
- **command** (optional): Specific build command to run (e.g. `pip install -e .[dev]`, `python -m build`)

## Hard Limits

- **Budget: 8 tool calls.** After 8 calls, stop and write your result immediately.
- **No full-project scans.** Only check specific files you suspect have issues.

## Approach

1. **Explore** (1-2 calls): Use `glob` to find `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`
2. **Read config** (1-2 calls): Use `read_file` to examine the main build configuration file
3. **Analyze** (0-2 calls): Check for common build issues — only read additional files if the config points to a specific problem
4. **Fix** (0-2 calls): If errors are found, use `edit_file` to fix them
5. **Write result** (1 call): Write the build result to the `result` output

Do NOT use MCP tools unless you have identified a specific file with a suspected issue. Never run linting or testing on the whole project.

## Common Build Issues

- Missing or incorrect package dependencies
- Version conflicts between dependencies
- Python version compatibility (syntax features, stdlib changes)
- Incorrect package discovery configuration
- Build backend misconfiguration (setuptools, hatch, flit, maturin)
- Missing or incorrect `__init__.py` files
- Circular imports preventing module loading

## Output

Write the build result to the `result` output:
- Build status (success/failure)
- Errors encountered and fixes applied
- Warnings worth addressing
