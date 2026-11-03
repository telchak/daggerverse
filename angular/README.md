# Angular - Dagger Module

Angular build, lint, test, and serve utilities for Dagger pipelines.

## Installation

```bash
# Install into your workspace (dagger.toml)
dagger module install github.com/telchak/daggerverse/angular@<version>

# Or add it as a dependency of your own module, from the module's directory
dagger module client add github.com/telchak/daggerverse/angular@<version> --sdk=python
```

## Functions

| Function | Description |
|----------|-------------|
| `build` | Build an Angular project and return the dist directory |
| `lint` | Lint an Angular project using ng lint |
| `test` | Run Angular project tests using ng test |
| `serve` | Start the Angular development server |
| `install` | Install Angular project dependencies |

## Checks

Installed in a workspace, the module checks the workspace's Angular project with `dagger check`, with no code of your own. The project is read from the workspace, not passed as an argument.

| Check | Runs |
|-------|------|
| `check-build` | `ng build --configuration production` |
| `check-lint` | `ng lint` (needs `@angular-eslint`) |
| `check-test` | `ng test --watch=false` in `node:<version>-slim` (no browser: suits the Vitest builder, not Karma) |

```bash
dagger module install github.com/telchak/daggerverse/angular@<version>
dagger check -l    # list the checks
dagger check       # run them
```

The project path and Node.js version are settings, and checks your project cannot run can be skipped, in `dagger.toml`:

```toml
[modules.angular.settings]
path = "frontend"
nodeVersion = "24"

[modules.angular.check]
skip = ["check-lint"]
```

## Caching

All functions mount an npm cache volume by default (`dag.cache_volume("angular-npm")`) to speed up repeated dependency installs. You can pass a custom cache volume to share across modules:

```python
# Share a single npm cache across angular and gcp-firebase
npm_cache = dag.cache_volume("my-shared-npm")

dist = await dag.angular().build(source=source, npm_cache=npm_cache)
output = await dag.angular().lint(source=source, npm_cache=npm_cache)
```

```bash
# CLI: caching is automatic, no extra flags needed
dagger api call angular build --source=.
```

## Usage

### Build

```bash
dagger api call angular build --source=. --configuration=production
```

### Python Example

```python
from dagger import dag

# Build
dist = await dag.angular().build(source=source)

# Lint
output = await dag.angular().lint(source=source, fix=True)

# Test
output = await dag.angular().test(source=source)

# Install dependencies
source_with_deps = dag.angular().install(source=source)
```

## License

Apache 2.0
