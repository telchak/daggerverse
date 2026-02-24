# Dagger Python SDK Guide

## GraphQL → Python Translation

| GraphQL | Python |
|---------|--------|
| `type MyModule` | `@object_type class MyModule:` |
| field/function | `@function` decorator on method |
| `String` | `str` |
| `Int` | `int` |
| `Boolean` | `bool` |
| `Float` | `float` |
| `[String!]!` | `list[str]` |
| `String!` (required) | parameter without default |
| `String` (optional) | `param: str \| None = None` |
| `Container` | `dagger.Container` |
| `Directory` | `dagger.Directory` |
| `File` | `dagger.File` |
| `Secret` | `dagger.Secret` |
| `Service` | `dagger.Service` |

## Module Structure

```
my-module/
  dagger.json          # {"name": "my-module", "sdk": {"source": "python"}, "engineVersion": "v0.19.11"}
  pyproject.toml       # dependencies
  src/my_module/
    __init__.py        # from .main import MyModule
    main.py            # @object_type class MyModule
```

## Key Patterns

```python
import dagger
from dagger import dag, function, object_type, field, Doc, DefaultPath
from typing import Annotated

@object_type
class MyModule:
    # Constructor field (set via CLI args)
    source: Annotated[dagger.Directory, Doc("Project source"), DefaultPath("/")] = field()

    @function
    async def build(self, target: str = "release") -> dagger.Container:
        """Build the project."""
        return (
            dag.container()
            .from_("python:3.13-slim")
            .with_directory("/app", self.source)
            .with_workdir("/app")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
        )
```

## Async/Await

All Dagger operations that fetch data are async. Chain builder methods synchronously,
await only when reading output:

```python
# Chaining (sync) — builds the pipeline
ctr = dag.container().from_("alpine").with_exec(["echo", "hi"])

# Reading output (async) — executes the pipeline
output = await ctr.stdout()
entries = await directory.entries()
contents = await file.contents()
```

## Services

```python
@function
def serve(self) -> dagger.Service:
    return (
        dag.container()
        .from_("nginx:alpine")
        .with_exposed_port(80)
        .as_service()
    )
```

## Caching

```python
cache = dag.cache_volume("pip-cache")
ctr = ctr.with_mounted_cache("/root/.cache/pip", cache)
```
