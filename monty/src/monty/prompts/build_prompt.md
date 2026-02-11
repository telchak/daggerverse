# Build Task

Build, lint, or type-check the Python project and diagnose any errors.

## Inputs Available

- **source**: Python project source directory
- **command** (optional): Specific build command to run (e.g. `pip install -e .[dev]`, `python -m build`)

## Approach

1. **Explore**: Use `glob` to find `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt` and understand the project setup
2. **Read config**: Use `read_file` to examine the main build configuration file
3. **Analyze**: Check for common build issues (missing dependencies, version conflicts, missing `__init__.py`, incorrect entry points)
4. **Use MCP sparingly**: Only use python-lft MCP to lint if you suspect a specific issue. Do NOT lint every file.
5. **Fix**: If errors are found, use `edit_file` to fix them

Aim for under 10 tool calls total.

## Common Build Issues

- Missing or incorrect package dependencies
- Version conflicts between dependencies
- Python version compatibility (syntax features, stdlib changes)
- Missing `py.typed` marker for typed packages
- Incorrect package discovery configuration
- Build backend misconfiguration (setuptools, hatch, flit, maturin)
- Missing or incorrect `__init__.py` files
- Circular imports preventing module loading
- Missing data files or package data configuration

## Output

Write the build result to the `result` output:
- Build status (success/failure)
- Errors encountered and fixes applied
- Warnings worth addressing
- Build configuration recommendations
