# Python Dependency Upgrade Task

Upgrade the package specified in **target_package** to the version specified in **target_version**.

## Inputs Available

- **target_package**: The package to upgrade (e.g. "django", "fastapi", "all")
- **target_version**: The target version (e.g. "5.0", "0.115.0", "latest")
- **source**: Python project source directory
- **dry_run** (optional): If "true", only analyze and report — do not modify files

## Approach

### Phase 1: Detect Current State

1. Read `pyproject.toml`, `setup.py`, `setup.cfg`, or `requirements*.txt` to identify the current version of the target package
2. Use pypi MCP to look up the target package's latest version and compatibility

### Phase 2: Analyze Impact

1. Use `grep` to find imports and usages of the target package in the project
2. Use pypi MCP to check for known breaking changes between current and target version
3. Categorize impact by severity (critical / warning / info)

**If dry_run is "true"**: Stop here. Write your analysis to `result`. Do NOT modify files, do NOT lint, do NOT read every file. Aim for 5-6 tool calls total.

### Phase 3: Apply Changes (skip if dry_run)

1. Update version constraints in the dependency file
2. Apply code modifications for breaking changes (update imports, replace removed APIs)
3. Read back modified files to confirm correctness

## Important Guidelines

- Always start by detecting the current version — never assume
- If upgrading "all", prioritize framework packages first, then utilities
- Preserve existing code style and conventions
- Do not modify test files unless the test framework itself requires changes
- Pay attention to peer dependency requirements
- If a dependency is not compatible with the target version, flag it clearly
- Check Python version compatibility of the target version

## Output

Write a detailed upgrade report to the `result` output:

### Current State
- Current package version and key dependencies

### Breaking Changes
- List of breaking changes between current and target version

### Impact Analysis
- Files affected and the specific changes needed

### Changes Applied (or Proposed if dry_run)
- List of files modified and what was changed

### Post-Upgrade Steps
- Manual steps the developer should take (e.g. `pip install -r requirements.txt`, running migrations)
- Dependencies that may need separate updates
- New features worth adopting
