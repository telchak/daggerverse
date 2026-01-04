"""Tests for semver module."""

import dagger
from dagger import dag


async def test_semver(source: dagger.Directory) -> str:
    """Run semver module tests."""
    results = []
    sv = dag.semver()

    prefix = "test-semver/"

    current = await sv.current(source=source, tag_prefix=prefix, initial_version="v0.0.0")
    results.append(f"PASS: current -> {current}")

    bumped = await sv.bump(source=source, tag_prefix=prefix, bump_type="patch", initial_version="v1.0.0")
    if not bumped.startswith("v1.0."):
        raise ValueError(f"Expected v1.0.x, got {bumped}")
    results.append(f"PASS: bump patch -> {bumped}")

    bump_type = await sv.bump_type(source=source, tag_prefix=prefix)
    if bump_type not in ["none", "patch", "minor", "major"]:
        raise ValueError(f"Invalid bump_type: {bump_type}")
    results.append(f"PASS: bump_type -> {bump_type}")

    return "\n".join(results)
