"""CalVer Module - Calendar Versioning utilities for Dagger pipelines."""

from datetime import datetime, timezone
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


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

        # Build version string with token replacement (use marker for MICRO)
        micro_marker = "{MICRO}"
        version = format
        version = version.replace("YYYY", str(now.year))
        version = version.replace("YY", str(now.year % 100))
        version = version.replace("0M", f"{now.month:02d}")
        version = version.replace("MM", str(now.month))
        version = version.replace("0D", f"{now.day:02d}")
        version = version.replace("DD", str(now.day))
        version = version.replace("MICRO", micro_marker)

        # Extract pattern (version with MICRO removed)
        pattern = version.replace(micro_marker, "")

        # Determine final MICRO value
        final_micro = micro
        if source and micro_marker in version:
            git_repo = source.as_git()

            # Check if HEAD commit already has a CalVer tag matching pattern
            existing_tag = await self._get_tag_for_head(git_repo, pattern)
            if existing_tag:
                print(f"Found existing tag on current commit: {existing_tag}")
                return existing_tag

            # No existing tag on HEAD, find max MICRO from all tags
            tags = await git_repo.tags()
            max_micro = -1
            for tag in tags:
                if tag.startswith(pattern):
                    remainder = tag[len(pattern):]
                    num_str = ""
                    for char in remainder:
                        if char.isdigit():
                            num_str += char
                        else:
                            break
                    if num_str:
                        max_micro = max(max_micro, int(num_str))

            final_micro = max_micro + 1

        # Replace MICRO marker with final value
        version = version.replace(micro_marker, str(final_micro))

        # Create and push the tag if requested
        if source and push_tag:
            await self._create_and_push_tag(source, version, github_token)

        return version

    async def _get_tag_for_head(self, git_repo: dagger.GitRepository, pattern: str) -> str | None:
        """Check if HEAD commit has a tag matching the CalVer pattern."""
        try:
            # Get current commit SHA
            head_sha = await git_repo.commit()

            # Get all tags
            tags = await git_repo.tags()

            # For each tag matching pattern, check if it points to HEAD
            for tag in tags:
                if tag.startswith(pattern):
                    tag_sha = await git_repo.tag(tag).commit()
                    if tag_sha == head_sha:
                        return tag
        except Exception:
            pass

        return None

    async def _create_and_push_tag(self, source: dagger.Directory, version: str, github_token: dagger.Secret | None) -> None:
        """Create and push a git tag to the remote repository."""
        try:
            git_container = (
                dag.container()
                .from_("alpine/git:latest")
                .with_mounted_directory("/repo", source)
                .with_workdir("/repo")
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

                    # Get token value
                    token_value = await github_token.plaintext()

                    # Set up authenticated URL and push
                    auth_url = f"https://x-access-token:{token_value}@github.com/{repo_path}.git"
                    await git_container.with_exec([
                        "git", "push", auth_url, version
                    ]).sync()

                    print(f"Created and pushed tag: {version}")
                else:
                    print(f"Warning: Non-GitHub remote, skipping push: {remote_url}")
            else:
                # Try to push without explicit token (relies on mounted git config)
                await git_container.with_exec(["git", "push", "origin", version]).sync()
                print(f"Created and pushed tag: {version}")

        except Exception as e:
            print(f"Warning: Could not push tag {version}: {e}")
