# GCP Firebase - Dagger Module

Firebase Hosting and Firestore database management utilities.

## Installation

```bash
dagger install github.com/telchak/daggerverse/gcp-firebase
```

## Features

- **Firebase Hosting**: Build and deploy web applications, preview channels
- **Firestore**: Create, update, delete, and manage Firestore databases

---

## Firebase Hosting

Firebase Hosting functions accept an `access_token` secret. Get one from a gcloud container:

```python
# Get access token from authenticated gcloud container
token = await gcloud.with_exec(["gcloud", "auth", "print-access-token"]).stdout()
access_token = dag.set_secret("firebase_token", token.strip())
```

### Functions

| Function | Description |
|----------|-------------|
| `build` | Build web application and return dist directory |
| `deploy` | Build and deploy to Firebase Hosting |
| `deploy-preview` | Deploy to a preview channel |
| `delete-channel` | Delete a preview channel |

### Usage

```python
from dagger import dag

# Get gcloud container from gcp-auth
gcloud = dag.gcp_auth().gcloud_container(
    credentials=credentials,
    project_id="my-project",
)

# Get access token
token = await gcloud.with_exec(["gcloud", "auth", "print-access-token"]).stdout()
access_token = dag.set_secret("firebase_token", token.strip())

# Deploy to production
result = await dag.gcp_firebase().deploy(
    access_token=access_token,
    project_id="my-firebase-project",
    source=source_dir,
    build_command="npm run build",
)

# Deploy preview
preview_url = await dag.gcp_firebase().deploy_preview(
    access_token=access_token,
    project_id="my-firebase-project",
    channel_id="pr-123",
    source=source_dir,
    expires="7d",
)

# Delete preview channel
await dag.gcp_firebase().delete_channel(
    access_token=access_token,
    project_id="my-firebase-project",
    channel_id="pr-123",
)
```

---

## Firestore Database Management

Firestore functions accept a pre-authenticated `gcloud` container.

See: https://firebase.google.com/docs/firestore/manage-databases

### Functions

| Function | Description |
|----------|-------------|
| `create` | Create a new Firestore database |
| `update` | Update database configuration (delete protection) |
| `delete` | Delete a Firestore database |
| `describe` | Get details of a database |
| `list` | List all databases in the project |
| `exists` | Check if a database exists |

### Usage

```python
from dagger import dag

# Get authenticated gcloud container from gcp-auth
gcloud = dag.gcp_auth().gcloud_container(
    credentials=credentials,
    project_id="my-project",
)

firestore = dag.gcp_firebase().firestore()

# Create a database
await firestore.create(
    gcloud=gcloud,
    database_id="my-database",
    location="us-central1",
)

# Check if exists
exists = await firestore.exists(
    gcloud=gcloud,
    database_id="my-database",
)

# Update delete protection
await firestore.update(
    gcloud=gcloud,
    database_id="my-database",
    delete_protection=True,
)

# Delete (must disable delete protection first)
await firestore.update(
    gcloud=gcloud,
    database_id="my-database",
    delete_protection=False,
)
await firestore.delete(
    gcloud=gcloud,
    database_id="my-database",
)
```

### CLI

```bash
# Create database
dagger call firestore create \
  --gcloud=FROM_GCP_AUTH \
  --database-id=my-database \
  --location=us-central1

# List databases
dagger call firestore list --gcloud=FROM_GCP_AUTH
```

## License

Apache 2.0
