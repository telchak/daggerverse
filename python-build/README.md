# Python Build - Dagger Module

Python build, lint, test, and typecheck utilities for Dagger pipelines.

## Installation

```bash
dagger install github.com/telchak/daggerverse/python-build
```

## Functions

| Function | Description |
|----------|-------------|
| `build` | Build a Python project and return the source with dist/ |
| `lint` | Lint a Python project (ruff, flake8, pylint) |
| `test` | Run tests (pytest, unittest) |
| `typecheck` | Type-check a Python project (mypy, pyright) |
| `install` | Install project dependencies |

## Usage

### Build

```bash
dagger call build --source=.
```

### Python Example

```python
from dagger import dag

# Build
result = await dag.python_build().build(source=source)

# Lint with ruff
output = await dag.python_build().lint(source=source, tool="ruff")

# Run tests
output = await dag.python_build().test(source=source)

# Type-check
output = await dag.python_build().typecheck(source=source, tool="mypy")

# Install dependencies
source_with_deps = await dag.python_build().install(source=source)
```

## License

Apache 2.0
