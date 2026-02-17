"""Examples for using the python-build Dagger module."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

_EXAMPLE_REPO = "https://github.com/nsidnev/fastapi-realworld-example-app.git"


@object_type
class PythonBuildExamples:
    """Usage examples for python-build module."""

    @function
    async def build_project(
        self,
        source: Annotated[dagger.Directory | None, Doc("Python project source")] = None,
    ) -> str:
        """Example: Build a Python project."""
        if source is None:
            source = dag.git(_EXAMPLE_REPO).branch("master").tree()

        result = await dag.python_build().build(source=source)
        entries = await result.entries()

        return f"Build succeeded: {len(entries)} entries"

    @function
    async def lint_project(
        self,
        source: Annotated[dagger.Directory | None, Doc("Python project source")] = None,
    ) -> str:
        """Example: Lint a Python project with ruff."""
        if source is None:
            source = dag.git(_EXAMPLE_REPO).branch("master").tree()

        output = await dag.python_build().lint(source=source, tool="ruff")
        return f"Lint output:\n{output}"

    @function
    async def install_deps(
        self,
        source: Annotated[dagger.Directory | None, Doc("Python project source")] = None,
    ) -> str:
        """Example: Install dependencies."""
        if source is None:
            source = dag.git(_EXAMPLE_REPO).branch("master").tree()

        result = await dag.python_build().install(source=source)
        entries = await result.entries()

        return f"Install succeeded: {len(entries)} entries"
