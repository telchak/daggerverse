"""Tests for calver module."""

from dagger import dag


async def test_calver() -> str:
    """Run calver module tests."""
    results = []
    calver = dag.calver()

    # Test default format
    version = await calver.generate()
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Expected 3 parts, got {len(parts)}: {version}")
    results.append(f"PASS: generate default -> {version}")

    # Test with micro
    version = await calver.generate(format="YYYY.MM.MICRO", micro=5)
    if not version.endswith(".5"):
        raise ValueError(f"Expected version to end with .5, got {version}")
    results.append(f"PASS: generate with micro -> {version}")

    # Test custom format
    version = await calver.generate(format="v.YY.0M.0D")
    if not version.startswith("v."):
        raise ValueError(f"Expected version to start with 'v.', got {version}")
    results.append(f"PASS: generate custom format -> {version}")

    return "\n".join(results)
