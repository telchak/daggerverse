# SemVer Module

Semantic Versioning utilities with [Conventional Commits](https://www.conventionalcommits.org/) support for Dagger pipelines.

## Features

- **Automatic version detection** from git tags
- **Conventional Commits parsing** to determine bump type
- **Monorepo support** with tag prefixes (e.g., `mymodule/v1.2.3`)
- **Tag creation and pushing** to GitHub

## Usage

### Calculate Next Version

```bash
# Analyze commits and calculate next version
dagger -m semver call next --source=.

# For monorepo with prefix
dagger -m semver call next --source=. --tag-prefix="mymodule/"
```

### Get Current Version

```bash
dagger -m semver call current --source=.
```

### Check Bump Type

```bash
# Returns: major, minor, patch, or none
dagger -m semver call bump-type --source=.
```

### Create Release Tag

```bash
dagger -m semver call release \
  --source=. \
  --github-token=env:GITHUB_TOKEN \
  --tag-prefix="mymodule/"
```

## Conventional Commits

The module analyzes commit messages to determine version bumps:

| Commit Type | Version Bump |
|-------------|--------------|
| `feat:` | Minor |
| `fix:` | Patch |
| `perf:` | Patch |
| `refactor:` | Patch |
| `BREAKING CHANGE:` | Major |
| `type!:` (with !) | Major |

### Examples

```bash
# Patch bump
git commit -m "fix: correct login validation"

# Minor bump
git commit -m "feat: add user profile page"

# Major bump
git commit -m "feat!: redesign API endpoints"
# or
git commit -m "feat: new auth system

BREAKING CHANGE: removed legacy auth tokens"
```

## Monorepo Support

For monorepos, use `--tag-prefix` to scope versions to specific modules:

```bash
# Tags will be: mymodule/v1.0.0, mymodule/v1.1.0, etc.
dagger -m semver call next --source=. --tag-prefix="mymodule/"
```

## API Reference

| Function | Description |
|----------|-------------|
| `next` | Calculate next version from conventional commits |
| `current` | Get current version from latest tag |
| `bump-type` | Analyze commits and return bump type |
| `bump` | Calculate next version with explicit bump type (ignores commits) |
| `release` | Calculate version and create git tag |
| `tag` | Create and push a git tag with specific version |
| `changed-paths` | List files changed since last tag |

### Manual Version Bumping

Use `bump` when you want to specify the exact bump type instead of analyzing commits:

```bash
# Explicit patch bump
dagger -m semver call bump --source=. --bump-type=patch

# Explicit minor bump
dagger -m semver call bump --source=. --bump-type=minor

# For monorepo
dagger -m semver call bump --source=. --bump-type=minor --tag-prefix="mymodule/"
```

### Manual Tagging

Use `tag` to create a tag with a specific version:

```bash
# Create and push a specific version tag
dagger -m semver call tag \
  --source=. \
  --version="v2.0.0" \
  --github-token=env:GITHUB_TOKEN

# For monorepo
dagger -m semver call tag \
  --source=. \
  --version="v1.5.0" \
  --tag-prefix="mymodule/" \
  --github-token=env:GITHUB_TOKEN
```
