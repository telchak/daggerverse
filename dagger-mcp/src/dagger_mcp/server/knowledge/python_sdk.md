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
| `Workspace` | `dagger.Workspace` (auto-populated from the caller's workspace) |
| `Changeset` | `dagger.Changeset` |
| `Void` | `None` |

## Module Structure

```
my-module/
  dagger-module.toml   # name + [entrypoint] (generated module) or [runtime] source = "python"
  pyproject.toml       # dependencies; uv.lock is committed
  src/my_module/
    __init__.py        # @object_type class MyModule (or: from .main import MyModule)
  sdk/                 # generated dagger-io library — committed
  clients/             # generated clients for core and each dependency — committed
```

The workspace's `dagger.toml` registers the module as a Python SDK scope
(`[sdks.python.scopes."my-module"] is-module = true`, `clients = [...]` for
dependencies). Run `dagger generate -y` after changing the module's API or its
dependencies, and commit the result. A Dagger 0.x module uses `dagger.json`
instead; Dagger 1.0 still loads it.

## Key Patterns

```python
import dagger
from dagger import check, dag, function, object_type

@object_type
class MyModule:
    source: dagger.Directory

    @classmethod
    def create(cls, ws: dagger.Workspace):
        # The caller's workspace is injected; nothing is uploaded until used
        return cls(source=ws.directory("/", exclude=["**/.git"]))

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

    @function
    @check
    async def test(self) -> None:
        """Run the tests: a check returns None and raises to fail."""
        await self.build().with_exec(["pytest"]).sync()
```

A `Workspace` argument is injected for CLI, `dagger check` and `dagger generate`
calls, but not when another module calls the function: pass one explicitly.

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
