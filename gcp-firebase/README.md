# GCP Firebase - Dagger Module

Firebase Hosting deployment utilities for web applications.

## Installation

```bash
dagger install github.com/YOUR_ORG/daggerverse/gcp-firebase
```

## Functions

| Function | Description |
|----------|-------------|
| `build` | Build web application and return dist directory |
| `deploy` | Build and deploy to Firebase Hosting |
| `deploy-preview` | Deploy to a preview channel |

## Usage

### Deploy to Production

```bash
dagger call deploy \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-firebase-project \
  --source=. \
  --build-command="npm run build"
```

### Deploy Preview

```bash
dagger call deploy-preview \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-firebase-project \
  --channel-id=pr-123 \
  --source=. \
  --expires=7d
```

### Python Example

```python
from dagger import dag

# Deploy to production
result = await dag.gcp_firebase().deploy(
    credentials=credentials,
    project_id="my-firebase-project",
    source=source_dir,
    build_command="npm run build",
)

# Deploy preview
preview_url = await dag.gcp_firebase().deploy_preview(
    credentials=credentials,
    project_id="my-firebase-project",
    channel_id="pr-123",
    source=source_dir,
    expires="7d",
)
```

## License

Apache 2.0
