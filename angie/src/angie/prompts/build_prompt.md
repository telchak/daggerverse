# Build Task

Build, compile, or lint the Angular project and diagnose any errors.

## Inputs Available

- **source**: Angular project source directory
- **command** (optional): Specific build command to run (e.g. `ng build --configuration production`)

## Approach

1. **Explore**: Use `glob` to find `angular.json`, `package.json`, `tsconfig.json` and understand the project setup
2. **Read config**: Use `read_file` to examine build configuration
3. **Analyze**: Check for common build issues:
   - Missing dependencies in `package.json`
   - TypeScript configuration errors in `tsconfig.json`
   - Angular configuration issues in `angular.json`
   - Import errors or circular dependencies
4. **Use MCP**: Use the Angular MCP build tool if available
5. **Fix**: If errors are found, use `edit_file` to fix them

## Common Build Issues

- Missing or incorrect module imports
- TypeScript strict mode violations
- Circular dependency warnings
- CSS/SCSS compilation errors
- Asset path configuration
- Environment file setup
- AOT compilation errors

## Output

Write the build result to the `result` output:
- Build status (success/failure)
- Errors encountered and fixes applied
- Warnings worth addressing
- Build configuration recommendations
