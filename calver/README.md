# CalVer - Dagger Module

Calendar Versioning (CalVer) utilities for Dagger pipelines.

## Features

- **Single function** for all versioning needs
- Generate CalVer version strings in any custom format
- **Include prefixes directly in format** (e.g., `v.YYYY.MM.MICRO`)
- Dynamic token replacement (supports unlimited format combinations)
- Auto-increment MICRO from git history (when source provided)
- Extremely simple and lightweight (63 lines, zero duplication)

## Installation

```bash
dagger install github.com/telchak/daggerverse/calver
```

## Quick Start

### Generate CalVer Version

```bash
# Generate current date version (YYYY.MM.DD)
dagger -m calver call generate
# Output: 2025.11.15

# Zero-padded format
dagger -m calver call generate --format="YYYY.0M.0D"
# Output: 2025.11.15

# With micro version
dagger -m calver call generate --format="YYYY.MM.DD" --micro=1
# Output: 2025.11.15.1

# Monthly versioning with auto-incrementing MICRO
dagger -m calver call generate --format="YYYY.MM.MICRO" --micro=5
# Output: 2025.11.5

# Auto-increment from git history (include prefix in format)
dagger -m calver call generate --source=. --format="v.YYYY.MM.MICRO"
# Output: v.2025.11.3 (if v.2025.11.0, v.2025.11.1, v.2025.11.2 exist)

# Short year format
dagger -m calver call generate --format="YY.0M"
# Output: 25.11
```

## Function

### `generate`

**One function does it all** - generates CalVer version strings with automatic git tag detection.

**Parameters:**
- `format` - CalVer format using tokens (default: `YYYY.MM.DD`)
  - See [Available Tokens](#available-tokens) below for all options
  - **Include prefixes directly in format** (e.g., `v.YYYY.MM.MICRO`)
- `micro` - Manual micro/patch version (default: `0`)
- `source` - Git repository directory (optional)
  - When provided with `MICRO` in format, auto-increments from git tags

**Returns:** Version string

**Usage Modes:**

```bash
# 1. Simple date-based version
dagger call generate --format="YYYY.0M.0D"
# Output: 2025.11.15

# 2. Manual MICRO version
dagger call generate --format="YYYY.MM.MICRO" --micro=5
# Output: 2025.11.5

# 3. Auto-increment MICRO from git (prefix in format)
dagger call generate --source=. --format="v.YYYY.MM.MICRO"
# Output: v.2025.11.3 (if tags v.2025.11.0, v.2025.11.1, v.2025.11.2 exist)
```

## Usage Examples

### Example 1: Use with Dagger's Container Publishing

```python
from dagger import dag, function, object_type

@object_type
class MyPipeline:
    @function
    async def build_and_publish(self, source: dagger.Directory):
        # Build container
        container = source.docker_build()

        # Get CalVer version
        version = dag.calver().generate(format="YYYY.0M.0D", micro=1)
        print(f"Publishing version: {version}")

        # Publish with CalVer tag
        ref = await container.publish(f"ghcr.io/myorg/myapp:{version}")

        return ref
```

### Example 2: Use with GCP Artifact Registry Module

```python
@object_type
class GcpPipeline:
    @function
    async def deploy(
        self,
        source: dagger.Directory,
        project_id: str,
        credentials: dagger.Secret,
    ):
        # Build container
        container = source.docker_build()

        # Generate CalVer version
        version = dag.calver().generate(format="YYYY.0M.0D", micro=1)
        print(f"Deploying version: {version}")

        # Publish to GCP Artifact Registry
        image_uri = await dag.gcp_artifact_registry().publish(
            container=container,
            project_id=project_id,
            repository="my-repo",
            image_name="my-image",
            tag=version,
            credentials=credentials,
        )

        return image_uri
```

### Example 3: Auto-increment from Git History

```python
@object_type
class ReleasePipeline:
    @function
    async def release(self, source: dagger.Directory):
        # Auto-increment MICRO based on git tags
        # If current month has v.2025.11.0, v.2025.11.1
        # This will return v.2025.11.2
        version = await dag.calver().generate(
            format="v.YYYY.MM.MICRO",
            source=source,
        )
        print(f"Next release: {version}")

        return version
```

### Example 4: Tag Git Commit (using git container)

```python
@object_type
class MyPipeline:
    @function
    async def tag_release(self, source: dagger.Directory):
        # Generate version with auto-increment (prefix in format)
        version = await dag.calver().generate(
            format="v.YYYY.MM.MICRO",
            source=source,
        )

        # Tag commit using git container
        result = await (
            dag.container()
            .from_("alpine/git:latest")
            .with_mounted_directory("/repo", source)
            .with_workdir("/repo")
            .with_exec(["git", "tag", version])
            .with_exec(["git", "push", "origin", version])
            .stdout()
        )

        return f"Tagged and pushed {version}"
```

## CalVer Formats

The module uses **dynamic token replacement**, so you can create any format combination you need.

### Available Tokens

| Token | Description | Example |
|-------|-------------|---------|
| `YYYY` | Full year (4 digits) | `2025` |
| `YY` | Short year (2 digits) | `25` |
| `MM` | Month (1-12) | `11` |
| `0M` | Zero-padded month (01-12) | `11` |
| `DD` | Day (1-31) | `15` |
| `0D` | Zero-padded day (01-31) | `15` |
| `MICRO` | Micro/patch version | `5` |

### Common Format Examples

| Format | Example | Description |
|--------|---------|-------------|
| `YYYY.MM.DD` | `2025.11.15` | Full year, month, day |
| `YYYY.0M.0D` | `2025.11.15` | Zero-padded month/day |
| `YYYY.MM.MICRO` | `2025.11.5` | Monthly releases with build counter |
| `YYYY.0M.MICRO` | `2025.11.5` | Zero-padded month with build counter |
| `YY.MM` | `25.11` | Short year, month |
| `YY.0M` | `25.11` | Short year, zero-padded month |

### Custom Format Examples

The dynamic approach supports **any combination**:

```bash
# ISO 8601 date format
dagger call generate --format="YYYY-0M-0D"
# Output: 2025-11-15

# Semantic versioning style
dagger call generate --format="YY.0M.MICRO" --micro=3
# Output: 25.11.3

# Custom prefix
dagger call generate --format="v.YYYY.MM.DD"
# Output: v.2025.11.15

# Compact format
dagger call generate --format="YYYYMMDD"
# Output: 20251115
```

**MICRO versioning:**
- Manual: `--format="YYYY.MM.MICRO" --micro=5` → `2025.11.5`
- Auto from git: `--source=. --format="v.YYYY.MM.MICRO"` → `v.2025.11.3`

**Note:** Prefixes like `v.` or `v` can be included directly in the format string!

## Best Practices

1. **Use YYYY.MM.MICRO for monthly releases**
   ```python
   # Automatically tracks builds per month
   # Month 1: 2025.11.0, 2025.11.1, 2025.11.2
   # Month 2: 2025.12.0, 2025.12.1 (resets to 0)
   version = await dag.calver().generate(
       format="YYYY.MM.MICRO",
       source=repo
   )
   ```

2. **Use zero-padding for sorting**
   ```bash
   # Good: sorts correctly
   2025.01.05, 2025.01.15, 2025.02.01

   # Bad: sorts incorrectly
   2025.1.5, 2025.1.15, 2025.2.1
   ```

3. **Micro versions for multiple releases per day**
   ```python
   # First release: 2025.11.15.0
   # Second release: 2025.11.15.1
   version = dag.calver().generate(micro=build_number)
   ```

4. **Consistent tag prefixes**
   ```bash
   # Good: all releases have 'v' prefix
   v2025.11.15, v2025.11.16

   # Bad: inconsistent
   2025.11.15, v2025.11.16
   ```

## Examples

The `examples/` directory contains concise, runnable examples in Python and Go:

```bash
# Python example (48 lines)
cd examples/python && dagger functions

# Go example (56 lines)
cd examples/go && dagger functions
```

Each example demonstrates a complete release workflow:
- Auto-incrementing MICRO from git tags
- Building and publishing containers
- Tagging git commits

## Related

- [CalVer Specification](https://calver.org/)
- [Dagger Documentation](https://docs.dagger.io/)

## License

Apache 2.0
