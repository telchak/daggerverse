"""Examples for using the semver Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class SemverExamples:
    """Usage examples for semver module."""

    @function
    async def calculate_next_version(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
    ) -> str:
        """Example: Calculate the next version based on conventional commits."""
        next_version = await dag.semver().next(source=source)
        current = await dag.semver().current(source=source)
        bump = await dag.semver().bump_type(source=source)

        return f"Current: {current} -> Next: {next_version} (bump: {bump})"

    @function
    async def monorepo_release(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
        module_name: Annotated[str, Doc("Module name (tag prefix)")],
        github_token: Annotated[dagger.Secret, Doc("GitHub token")],
    ) -> str:
        """Example: Release a specific module in a monorepo."""
        tag_prefix = f"{module_name}/"

        # Create the release
        result = await dag.semver().release(
            source=source,
            github_token=github_token,
            tag_prefix=tag_prefix,
        )

        return f"Released {module_name}: {result}"

    @function
    async def check_changes(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
        tag_prefix: Annotated[str, Doc("Tag prefix")] = "",
    ) -> str:
        """Example: Check what files changed since last release."""
        changed = await dag.semver().changed_paths(
            source=source,
            tag_prefix=tag_prefix,
        )

        if not changed:
            return "No changes since last release"

        files = changed.split("\n")
        return f"Changed files ({len(files)}):\n{changed}"
