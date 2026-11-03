# Build Task

Build the Angular project using the deterministic build tool.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **workspace**: the project source, which the workspace tools read and edit
- **command** (optional): Specific build configuration override

## Hard Limits

- **Budget: 12 tool calls.** After 12 calls, stop and write your result immediately.
- **Max 3 build attempts.** Do not retry more than 3 times.

## Approach

1. **Build** (1 call): Call `angularBuild(source=<workspace>)` to run the actual `ng build`
2. **Check result**: If the build succeeds, you're done — return the workspace
3. **Diagnose** (if failed): Read the error output, identify the failing file(s)
4. **Fix** (1-3 calls): Use `readFile` and `editFile` to fix the issue
5. **Retry** (1 call): Call `angularBuild` again to verify the fix
6. Repeat steps 3-5 up to 3 times total

## Available Tools

- `angularBuild(source, configuration, output_path)` — Run `ng build`, returns dist directory
- `angularLint(source, fix)` — Run `ng lint`, returns output
- `angularTest(source)` — Run `ng test`, returns output
- `angularInstall(source)` — Run `npm ci`, returns source with node_modules
- `readFile(file_path)` — Read a file from the workspace
- `editFile(file_path, old_string, new_string)` — Edit a file in the workspace
- `glob(pattern)` — Find files matching a pattern
- `grep(pattern)` — Search file contents

## Common Build Fixes

- Missing imports: add the missing import statement
- TypeScript strict mode: add type annotations or null checks
- Missing dependencies: check package.json
- Angular configuration: check angular.json

## Output

The build result is the returned workspace directory. Do NOT write diagnostic reports or markdown files.
