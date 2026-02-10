# Angular Version Upgrade Task

Upgrade the Angular project to the target version specified in the **target_version** input.

## Inputs Available

- **target_version**: The Angular version to upgrade to (e.g. "19", "18.2", "20.0.0")
- **source**: Angular project source directory
- **dry_run** (optional): If "true", only analyze and report — do not modify files

## Approach

### Phase 1: Detect Current State

1. Read `package.json` to identify the current Angular version (`@angular/core`, `@angular/cli`)
2. Read `angular.json` to understand the project configuration
3. Read `tsconfig.json` for TypeScript configuration
4. Use `glob` to get an overview of the project structure (components, services, modules, etc.)
5. Check for other Angular-related dependencies (`@angular/material`, `@ngrx/store`, `rxjs`, etc.)

### Phase 2: Research Breaking Changes

1. Use the Angular MCP tools to look up the official migration guide between the current and target versions
2. Use the Angular MCP modernize tool to identify available automated migrations
3. Identify key breaking changes including:
   - Removed or renamed APIs
   - Changed default behaviors
   - New required dependencies
   - TypeScript version requirements
   - Node.js version requirements
   - RxJS version compatibility
   - Third-party library compatibility (Angular Material, NgRx, etc.)

### Phase 3: Analyze Codebase Impact

1. For each breaking change, use `grep` to find affected code in the project
2. Categorize findings by severity:
   - **Critical**: Code that will fail to compile or cause runtime errors
   - **Warning**: Deprecated APIs that still work but should be updated
   - **Info**: Opportunities to adopt new patterns (signals, control flow, etc.)
3. Check `angular.json` for configuration changes needed
4. Check `tsconfig.json` for TypeScript version compatibility

### Phase 4: Apply Changes (skip if dry_run)

1. Update `package.json` dependencies to target versions
2. Apply code modifications for each breaking change:
   - Update imports
   - Replace removed/renamed APIs
   - Update TypeScript patterns
   - Migrate to new Angular patterns where required
3. Update `angular.json` configuration if needed
4. Update `tsconfig.json` if TypeScript version changes

### Phase 5: Verification

1. Read back modified files to confirm correctness
2. Check for remaining references to deprecated/removed APIs
3. Verify import paths are correct

## Important Guidelines

- Always start by detecting the current version — never assume
- Handle multi-step upgrades: if jumping multiple major versions (e.g. 15 → 19), note that Angular recommends upgrading one major version at a time, and list the intermediate steps
- Preserve existing code style and conventions
- Do not modify test files unless the test framework itself requires changes
- When updating `package.json`, update both dependencies and devDependencies
- Pay attention to peer dependency requirements
- If a third-party library is not compatible with the target version, flag it clearly

## Output

Write a detailed upgrade report to the `result` output:

### Current State
- Current Angular version and key dependencies

### Breaking Changes
- List of breaking changes between current and target version

### Impact Analysis
- Files affected and the specific changes needed

### Changes Applied (or Proposed if dry_run)
- List of files modified and what was changed

### Post-Upgrade Steps
- Manual steps the developer should take (e.g. `npm install`, `ng update`, testing)
- Third-party libraries that may need separate updates
- New features worth adopting
