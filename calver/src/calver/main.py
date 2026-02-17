"""CalVer Module - Calendar Versioning utilities for Dagger pipelines."""

import logging
from datetime import datetime, timezone
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


# Configure module logger
_logger = logging.getLogger(__name__)

# Default container images
_GIT_IMAGE = "alpine/git:latest"
_REPO_WORKDIR = "/repo"


@object_type
class Calver:
    """Calendar Versioning (CalVer) utilities."""

    @function
    async def generate(
        self,
        format: Annotated[str, Doc("CalVer format (YYYY.MM.DD, v.YYYY.MM.MICRO, etc.)")] = "YYYY.MM.DD",
        micro: Annotated[int, Doc("Manual micro/patch version")] = 0,
        source: Annotated[dagger.Directory | None, Doc("Git repo (enables auto-increment)")] = None,
        push_tag: Annotated[bool, Doc("Push generated tag to remote repository")] = False,
        github_token: Annotated[dagger.Secret | None, Doc("GitHub token for pushing tags")] = None,
    ) -> str:
        """Generate CalVer version string based on current date.

        If the current commit already has a CalVer tag matching the pattern,
        that existing tag is returned (preventing duplicate tags on same commit).
        Otherwise, generates a new version and optionally pushes the tag.
        """
        now = datetime.now(timezone.utc)
        version = self._apply_version_tokens(format, now)

        micro_marker = "{MICRO}"
        pattern = version.replace(micro_marker, "")

        # Determine final MICRO value
        final_micro = micro
        if source and micro_marker in version:
            existing_tag = await self._get_tag_for_head(source, pattern)
            if existing_tag:
                _logger.info("Found existing tag on current commit: %s", existing_tag)
                return existing_tag

            tags = await source.as_git().tags()
            final_micro = self._find_max_micro(tags, pattern) + 1

        version = version.replace(micro_marker, str(final_micro))

        if source and push_tag:
            await self._create_and_push_tag(source, version, github_token)

        return version

    @staticmethod
    def _apply_version_tokens(format: str, now: datetime) -> str:
        """Replace date tokens in the format string, leaving MICRO as a placeholder."""
        version = format
        version = version.replace("YYYY", str(now.year))
        version = version.replace("YY", str(now.year % 100))
        version = version.replace("0M", f"{now.month:02d}")
        version = version.replace("MM", str(now.month))
        version = version.replace("0D", f"{now.day:02d}")
        version = version.replace("DD", str(now.day))
        version = version.replace("MICRO", "{MICRO}")
        return version

    @staticmethod
    def _find_max_micro(tags: list[str], prefix: str) -> int:
        """Find the highest MICRO value among tags matching the given prefix."""
        max_micro = -1
        for tag in tags:
            if tag.startswith(prefix):
                remainder = tag[len(prefix):]
                num_str = ""
                for char in remainder:
                    if char.isdigit():
                        num_str += char
                    else:
                        break
                if num_str:
                    max_micro = max(max_micro, int(num_str))
        return max_micro

    async def _get_tag_for_head(
        self,
        source: dagger.Directory,
        pattern: str,
    ) -> str | None:
        """Check if HEAD commit has a tag matching the CalVer pattern.

        Uses git directly to find tags pointing at HEAD, which is more reliable
        than using the Dagger GitRepository API in CI environments.

        Args:
            source: Git repository directory
            pattern: CalVer pattern prefix to match (e.g., "2024.01.")

        Returns:
            The matching tag if found, None otherwise
        """
        try:
            # Use git directly to find all tags pointing at HEAD
            result = await (
                dag.container()
                .from_(_GIT_IMAGE)
                .with_mounted_directory(_REPO_WORKDIR, source)
                .with_workdir(_REPO_WORKDIR)
                .with_exec(["git", "tag", "--points-at", "HEAD"])
                .stdout()
            )

            # Check each tag to see if it matches our CalVer pattern
            for tag in result.strip().split("\n"):
                tag = tag.strip()
                if tag and tag.startswith(pattern):
                    return tag
        except Exception:
            # Don't expose exception details which may contain sensitive information
            _logger.warning("Could not check tags on HEAD")

        return None

    async def _create_and_push_tag(
        self,
        source: dagger.Directory,
        version: str,
        github_token: dagger.Secret | None,
    ) -> None:
        """Create and push a git tag to the remote repository.

        Args:
            source: Git repository directory
            version: Version string to use as the tag name
            github_token: GitHub token for authenticated push (optional)

        Raises:
            No exceptions raised - failures are logged as warnings
        """
        try:
            git_container = (
                dag.container()
                .from_(_GIT_IMAGE)
                .with_mounted_directory(_REPO_WORKDIR, source)
                .with_workdir(_REPO_WORKDIR)
            )

            # Create the tag
            git_container = await git_container.with_exec(["git", "tag", version]).sync()

            # Push the tag to remote
            if github_token:
                # Get the remote URL and extract repo info
                remote_url = await git_container.with_exec(["git", "remote", "get-url", "origin"]).stdout()
                remote_url = remote_url.strip()

                # Configure git with token authentication
                # Extract owner/repo from URL (handles both HTTPS and SSH URLs)
                if "github.com" in remote_url:
                    # Convert SSH URL to HTTPS if needed
                    if remote_url.startswith("git@github.com:"):
                        repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
                    else:
                        # HTTPS URL - extract path
                        repo_path = remote_url.split("github.com/")[1].replace(".git", "")

                    # Push using token via environment variable to avoid exposing in command args
                    await (
                        git_container
                        .with_secret_variable("GH_TOKEN", github_token)
                        .with_exec([
                            "sh", "-c",
                            f'git push "https://x-access-token:$GH_TOKEN@github.com/{repo_path}.git" {version}'
                        ])
                        .sync()
                    )

                    _logger.info("Created and pushed tag: %s", version)
                else:
                    # Don't expose the remote URL which may contain sensitive information
                    _logger.warning("Non-GitHub remote detected, skipping push")
            else:
                # Try to push without explicit token (relies on mounted git config)
                await git_container.with_exec(["git", "push", "origin", version]).sync()
                _logger.info("Created and pushed tag: %s", version)

        except Exception:
            # Don't expose exception details which may contain sensitive information
            _logger.warning("Could not push tag %s", version)
