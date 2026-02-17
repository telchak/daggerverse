# Build Task

Build the Angular project using the deterministic build tool.

## Inputs Available

- **source**: Angular project source directory (in your workspace)
- **command** (optional): Specific build configuration override

## Hard Limits

- **Budget: 12 tool calls.** After 12 calls, stop and write your result immediately.
- **Max 3 build attempts.** Do not retry more than 3 times.

## Approach

1. **Build** (1 call): Call `angular_build(source=<workspace>)` to run the actual `ng build`
2. **Check result**: If the build succeeds, you're done — return the workspace
3. **Diagnose** (if failed): Read the error output, identify the failing file(s)
4. **Fix** (1-3 calls): Use `read_file` and `edit_file` to fix the issue
5. **Retry** (1 call): Call `angular_build` again to verify the fix
6. Repeat steps 3-5 up to 3 times total

## Available Tools

- `angular_build(source, configuration, output_path)` — Run `ng build`, returns dist directory
- `angular_lint(source, fix)` — Run `ng lint`, returns output
- `angular_test(source)` — Run `ng test`, returns output
- `angular_install(source)` — Run `npm ci`, returns source with node_modules
- `read_file(file_path)` — Read a file from the workspace
- `edit_file(file_path, old_string, new_string)` — Edit a file in the workspace
- `glob(pattern)` — Find files matching a pattern
- `grep(pattern)` — Search file contents

## Common Build Fixes

- Missing imports: add the missing import statement
- TypeScript strict mode: add type annotations or null checks
- Missing dependencies: check package.json
- Angular configuration: check angular.json

## Output

The build result is the returned workspace directory. Do NOT write diagnostic reports or markdown files.
