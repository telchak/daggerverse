# Angular - Dagger Module

Angular build, lint, test, and serve utilities for Dagger pipelines.

## Installation

```bash
dagger install github.com/telchak/daggerverse/angular
```

## Functions

| Function | Description |
|----------|-------------|
| `build` | Build an Angular project and return the dist directory |
| `lint` | Lint an Angular project using ng lint |
| `test` | Run Angular project tests using ng test |
| `serve` | Start the Angular development server |
| `install` | Install Angular project dependencies |

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
dagger call build --source=.
```

## Usage

### Build

```bash
dagger call build --source=. --configuration=production
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
