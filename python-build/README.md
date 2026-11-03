# Python Build - Dagger Module

Python build, lint, test, and typecheck utilities for Dagger pipelines.

## Installation

```bash
# Install into your workspace (dagger.toml)
dagger module install github.com/telchak/daggerverse/python-build@<version>

# Or add it as a dependency of your own module, from the module's directory
dagger module client add github.com/telchak/daggerverse/python-build@<version> --sdk=python
```

## Functions

| Function | Description |
|----------|-------------|
| `build` | Build a Python project and return the source with dist/ |
| `lint` | Lint a Python project (ruff, flake8, pylint) |
| `test` | Run tests (pytest, unittest) |
| `typecheck` | Type-check a Python project (mypy, pyright) |
| `install` | Install project dependencies |

## Checks

Installed in a workspace, the module checks the workspace's Python project with `dagger check`, with no code of your own. The project is read from the workspace, not passed as an argument.

| Check | Runs |
|-------|------|
| `check-lint` | `ruff check .` |
| `check-test` | `python -m pytest`, after installing the project's dependencies |
| `check-typecheck` | `python -m mypy .`, after installing the project's dependencies |
| `check-build` | `python -m build` |

```bash
dagger module install github.com/telchak/daggerverse/python-build@<version>
dagger check -l    # list the checks
dagger check       # run them
```

The project path and Python version are settings, and checks your project cannot run can be skipped, in `dagger.toml`:

```toml
[modules.python-build.settings]
path = "backend"
pythonVersion = "3.12"

[modules.python-build.check]
skip = ["check-typecheck"]
```

## Caching

All functions mount pip and uv cache volumes by default (`dag.cache_volume("python-pip")` and `dag.cache_volume("python-uv")`) to speed up repeated dependency installs. You can pass custom cache volumes to share across modules:

```python
# Share cache volumes across python-build and other Python modules
pip_cache = dag.cache_volume("my-shared-pip")
uv_cache = dag.cache_volume("my-shared-uv")

result = await dag.python_build().build(source=source, pip_cache=pip_cache, uv_cache=uv_cache)
output = await dag.python_build().lint(source=source, pip_cache=pip_cache, uv_cache=uv_cache)
```

```bash
# CLI: caching is automatic, no extra flags needed
dagger api call python-build build --source=.
```

## Usage

### Build

```bash
dagger api call python-build build --source=.
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
