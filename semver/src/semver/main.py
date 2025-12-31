"""SemVer Module - Semantic Versioning with Conventional Commits for Dagger pipelines."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


class BumpType(Enum):
    """Version bump types."""
    NONE = "none"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


@dataclass
class Version:
    """Semantic version representation."""
    major: int
    minor: int
    patch: int
    prefix: str = "v"

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse version string like 'v1.2.3' or '1.2.3'."""
        prefix = ""
        if version_str.startswith("v"):
            prefix = "v"
            version_str = version_str[1:]

        match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version_str)
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prefix=prefix,
        )

    def bump(self, bump_type: BumpType) -> "Version":
        """Return new version with bump applied."""
        if bump_type == BumpType.MAJOR:
            return Version(self.major + 1, 0, 0, self.prefix)
        elif bump_type == BumpType.MINOR:
            return Version(self.major, self.minor + 1, 0, self.prefix)
        elif bump_type == BumpType.PATCH:
            return Version(self.major, self.minor, self.patch + 1, self.prefix)
        return self

    def __str__(self) -> str:
        return f"{self.prefix}{self.major}.{self.minor}.{self.patch}"


@object_type
class Semver:
    """Semantic Versioning utilities with Conventional Commits support."""

    @function
    async def next(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
        tag_prefix: Annotated[str, Doc("Tag prefix for monorepo (e.g., 'mymodule/')")] = "",
        default_bump: Annotated[str, Doc("Default bump if no conventional commits found")] = "patch",
        initial_version: Annotated[str, Doc("Initial version if no tags exist")] = "0.1.0",
    ) -> str:
        """Calculate next semantic version based on conventional commits.

        Analyzes commits since the last tag to determine the version bump:
        - BREAKING CHANGE or ! → major
        - feat: → minor
        - fix:, perf:, refactor: → patch

        For monorepos, use tag_prefix to filter tags and commits by path.
        """
        # Get commits and determine bump type
        bump_type = await self._analyze_commits(source, tag_prefix)

        if bump_type == BumpType.NONE:
            bump_type = BumpType[default_bump.upper()]

        # Get current version from tags
        current = await self._get_latest_version(source, tag_prefix, initial_version)

        # Calculate next version
        next_version = current.bump(bump_type)

        return str(next_version)

    @function
    async def bump_type(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
        tag_prefix: Annotated[str, Doc("Tag prefix for monorepo")] = "",
    ) -> str:
        """Analyze commits and return the bump type (major/minor/patch/none)."""
        result = await self._analyze_commits(source, tag_prefix)
        return result.value

    @function
    async def current(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
        tag_prefix: Annotated[str, Doc("Tag prefix for monorepo")] = "",
        initial_version: Annotated[str, Doc("Version if no tags exist")] = "0.0.0",
    ) -> str:
        """Get the current version from the latest matching tag."""
        version = await self._get_latest_version(source, tag_prefix, initial_version)
        return str(version)

    @function
    async def release(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
        github_token: Annotated[dagger.Secret, Doc("GitHub token for pushing tags")],
        tag_prefix: Annotated[str, Doc("Tag prefix for monorepo")] = "",
        default_bump: Annotated[str, Doc("Default bump if no conventional commits")] = "patch",
        initial_version: Annotated[str, Doc("Initial version if no tags exist")] = "0.1.0",
        dry_run: Annotated[bool, Doc("Calculate version without creating tag")] = False,
    ) -> str:
        """Calculate next version and create a git tag.

        Returns the new version tag that was created (or would be created if dry_run).
        """
        next_version = await self.next(source, tag_prefix, default_bump, initial_version)
        tag_name = f"{tag_prefix}{next_version}"

        if dry_run:
            return f"[dry-run] Would create tag: {tag_name}"

        # Check if HEAD already has this tag
        existing = await self._get_tag_for_head(source, tag_prefix)
        if existing:
            return f"HEAD already tagged: {existing}"

        # Create and push the tag
        await self._create_and_push_tag(source, tag_name, github_token)

        return tag_name

    @function
    async def changed_paths(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository")],
        tag_prefix: Annotated[str, Doc("Tag prefix to find last release")] = "",
    ) -> str:
        """List paths that changed since the last tag.

        Useful for detecting which modules in a monorepo need releases.
        Returns newline-separated list of changed file paths.
        """
        git = self._git_container(source)

        # Get the last tag
        last_tag = await self._get_latest_tag(source, tag_prefix)

        if last_tag:
            # Get diff since last tag
            diff_output = await (
                git.with_exec(["git", "diff", "--name-only", f"{last_tag}..HEAD"])
                .stdout()
            )
        else:
            # No tag, get all files
            diff_output = await (
                git.with_exec(["git", "ls-files"])
                .stdout()
            )

        return diff_output.strip()

    async def _analyze_commits(self, source: dagger.Directory, tag_prefix: str) -> BumpType:
        """Analyze commits since last tag to determine bump type."""
        git = self._git_container(source)

        # Get the last tag for this prefix
        last_tag = await self._get_latest_tag(source, tag_prefix)

        # Get commit messages since last tag
        if last_tag:
            log_output = await (
                git.with_exec(["git", "log", f"{last_tag}..HEAD", "--format=%s%n%b", "--"])
                .stdout()
            )
        else:
            # No previous tag, analyze all commits
            log_output = await (
                git.with_exec(["git", "log", "--format=%s%n%b"])
                .stdout()
            )

        return self._parse_conventional_commits(log_output)

    def _parse_conventional_commits(self, log_output: str) -> BumpType:
        """Parse commit messages and determine bump type."""
        bump = BumpType.NONE

        # Patterns for conventional commits
        breaking_pattern = re.compile(r"^BREAKING CHANGE:|^[a-z]+(\([^)]+\))?!:")
        feat_pattern = re.compile(r"^feat(\([^)]+\))?:")
        patch_pattern = re.compile(r"^(fix|perf|refactor)(\([^)]+\))?:")

        for line in log_output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check for breaking changes (highest priority)
            if breaking_pattern.match(line) or "BREAKING CHANGE" in line:
                return BumpType.MAJOR

            # Check for features
            if feat_pattern.match(line):
                bump = BumpType.MINOR

            # Check for patches (only upgrade if not already minor)
            if patch_pattern.match(line) and bump == BumpType.NONE:
                bump = BumpType.PATCH

        return bump

    async def _get_latest_tag(self, source: dagger.Directory, tag_prefix: str) -> str | None:
        """Get the latest tag matching the prefix."""
        git = self._git_container(source)

        try:
            if tag_prefix:
                # List tags matching prefix, sort by version
                tags_output = await (
                    git.with_exec([
                        "sh", "-c",
                        f"git tag -l '{tag_prefix}v*' | sort -V | tail -n 1"
                    ])
                    .stdout()
                )
            else:
                # Get latest tag overall
                tags_output = await (
                    git.with_exec([
                        "sh", "-c",
                        "git tag -l 'v*' | sort -V | tail -n 1"
                    ])
                    .stdout()
                )

            tag = tags_output.strip()
            return tag if tag else None
        except Exception:
            return None

    async def _get_latest_version(
        self, source: dagger.Directory, tag_prefix: str, initial: str
    ) -> Version:
        """Get the latest version from tags, or return initial version."""
        tag = await self._get_latest_tag(source, tag_prefix)

        if not tag:
            return Version.parse(initial)

        # Remove prefix to get version
        version_str = tag
        if tag_prefix and tag.startswith(tag_prefix):
            version_str = tag[len(tag_prefix):]

        return Version.parse(version_str)

    async def _get_tag_for_head(self, source: dagger.Directory, tag_prefix: str) -> str | None:
        """Check if HEAD has a tag matching the prefix."""
        git = self._git_container(source)

        try:
            pattern = f"{tag_prefix}v*" if tag_prefix else "v*"
            tag_output = await (
                git.with_exec([
                    "sh", "-c",
                    f"git tag --points-at HEAD | grep -E '^{re.escape(tag_prefix)}v[0-9]' | head -n 1"
                ])
                .stdout()
            )
            tag = tag_output.strip()
            return tag if tag else None
        except Exception:
            return None

    async def _create_and_push_tag(
        self, source: dagger.Directory, tag: str, github_token: dagger.Secret
    ) -> None:
        """Create and push a git tag."""
        git = self._git_container(source)

        # Create annotated tag
        git = await git.with_exec(["git", "tag", "-a", tag, "-m", f"Release {tag}"]).sync()

        # Get remote URL
        remote_url = await git.with_exec(["git", "remote", "get-url", "origin"]).stdout()
        remote_url = remote_url.strip()

        if "github.com" not in remote_url:
            raise ValueError(f"Non-GitHub remote not supported: {remote_url}")

        # Extract repo path
        if remote_url.startswith("git@github.com:"):
            repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
        else:
            repo_path = remote_url.split("github.com/")[1].replace(".git", "")

        # Push with token auth
        token = await github_token.plaintext()
        auth_url = f"https://x-access-token:{token}@github.com/{repo_path}.git"

        await git.with_exec(["git", "push", auth_url, tag]).sync()

    def _git_container(self, source: dagger.Directory) -> dagger.Container:
        """Create a container with git and the source mounted."""
        return (
            dag.container()
            .from_("alpine/git:latest")
            .with_mounted_directory("/repo", source)
            .with_workdir("/repo")
        )
