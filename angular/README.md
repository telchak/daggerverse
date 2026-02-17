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
