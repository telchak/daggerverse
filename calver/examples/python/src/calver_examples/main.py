"""Example using CalVer module to version and publish container releases."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class CalverExamples:
    """CalVer module usage example."""

    @function
    async def release(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with git")],
        registry: Annotated[str, Doc("Container registry")] = "ghcr.io/myorg/myapp",
    ) -> str:
        """Build, version, and publish container with auto-incremented CalVer tag.

        This example demonstrates:
        - Auto-incrementing MICRO from git tags (v.2025.11.0 -> v.2025.11.1)
        - Building a container
        - Publishing with CalVer tag
        - Tagging and pushing to git
        """
        # Generate auto-incremented version from git history
        version = await dag.calver().generate(
            format="v.YYYY.MM.MICRO",
            source=source,
        )

        # Build and publish container
        container = source.docker_build()
        ref = await container.publish(f"{registry}:{version}")

        # Tag git commit
        await (
            dag.container()
            .from_("alpine/git:latest")
            .with_mounted_directory("/repo", source)
            .with_workdir("/repo")
            .with_exec(["git", "tag", version])
            .with_exec(["git", "push", "origin", version])
            .sync()
        )

        return f"Released {version} -> {ref}"
