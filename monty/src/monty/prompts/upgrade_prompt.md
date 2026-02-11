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
2. Use `glob` to get an overview of the project structure
3. Check for other related dependencies that might need co-upgrading
4. Identify the Python version constraints
5. Use pypi MCP tools to look up the target package's latest versions and compatibility

### Phase 2: Research Breaking Changes

1. Use pypi MCP tools to get package info, dependencies, and version history
2. Identify key breaking changes including:
   - Removed or renamed APIs
   - Changed default behaviors
   - New required dependencies
   - Python version requirements
   - Deprecated features that were removed
   - Configuration format changes

### Phase 3: Analyze Codebase Impact

1. For each breaking change, use `grep` to find affected code in the project
2. Categorize findings by severity:
   - **Critical**: Code that will fail at import or runtime
   - **Warning**: Deprecated APIs that still work but should be updated
   - **Info**: Opportunities to adopt new patterns and features
3. Check configuration files for format changes needed
4. Check for affected test code

### Phase 4: Apply Changes (skip if dry_run)

1. Update version constraints in `pyproject.toml`, `requirements.txt`, or equivalent
2. Apply code modifications for each breaking change:
   - Update imports
   - Replace removed/renamed APIs
   - Update configuration patterns
   - Migrate to new APIs where required
3. Update related dependencies if needed (e.g. upgrading Django may require upgrading djangorestframework)

### Phase 5: Verification

1. Read back modified files to confirm correctness
2. Check for remaining references to deprecated/removed APIs
3. Verify import paths are correct
4. Use python-lft MCP tools to lint the modified code

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
