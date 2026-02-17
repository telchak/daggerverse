"""Examples for using the angular Dagger module."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

_EXAMPLE_REPO = "https://github.com/realworld-apps/angular-realworld-example-app.git"


@object_type
class AngularExamples:
    """Usage examples for angular module."""

    @function
    async def build_project(
        self,
        source: Annotated[dagger.Directory | None, Doc("Angular project source")] = None,
    ) -> str:
        """Example: Build an Angular project for production."""
        if source is None:
            source = dag.git(_EXAMPLE_REPO).branch("main").tree()

        dist = await dag.angular().build(source=source, configuration="production")
        entries = await dist.entries()

        return f"Build succeeded: {len(entries)} files in dist/"

    @function
    async def lint_project(
        self,
        source: Annotated[dagger.Directory | None, Doc("Angular project source")] = None,
    ) -> str:
        """Example: Lint an Angular project."""
        if source is None:
            source = dag.git(_EXAMPLE_REPO).branch("main").tree()

        output = await dag.angular().lint(source=source)
        return f"Lint output:\n{output}"

    @function
    async def install_deps(
        self,
        source: Annotated[dagger.Directory | None, Doc("Angular project source")] = None,
    ) -> str:
        """Example: Install dependencies and verify node_modules."""
        if source is None:
            source = dag.git(_EXAMPLE_REPO).branch("main").tree()

        result = dag.angular().install(source=source)
        entries = await result.entries()
        has_modules = "node_modules" in entries

        return f"Install succeeded: node_modules={has_modules}, {len(entries)} entries"
