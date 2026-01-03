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

### Functions

| Function | Description |
|----------|-------------|
| `build` | Build web application and return dist directory |
| `deploy` | Build and deploy to Firebase Hosting |
| `deploy-preview` | Deploy to a preview channel |
| `delete-channel` | Delete a preview channel |

### Usage

#### Deploy to Production

```bash
dagger call deploy \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-firebase-project \
  --source=. \
  --build-command="npm run build"
```

#### Deploy Preview

```bash
dagger call deploy-preview \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-firebase-project \
  --channel-id=pr-123 \
  --source=. \
  --expires=7d
```

#### Delete Preview Channel

```bash
dagger call delete-channel \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-firebase-project \
  --channel-id=pr-123
```

#### Python Example

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

# Delete preview channel
await dag.gcp_firebase().delete_channel(
    credentials=credentials,
    project_id="my-firebase-project",
    channel_id="pr-123",
)
```

---

## Firestore Database Management

Manage Firestore databases using gcloud CLI commands.

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

#### Create a Database

```bash
dagger call firestore create \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project \
  --database-id=my-database \
  --location=us-central1 \
  --database-type=firestore-native \
  --delete-protection=false
```

**Parameters:**
- `database-id`: Lowercase letters, numbers, hyphens (4-63 characters, starting with letter)
- `location`: Region (e.g., `us-central1`) or multi-region (e.g., `nam5`, `eur3`)
- `database-type`: `firestore-native` (default) or `datastore-mode`
- `delete-protection`: Enable to prevent accidental deletion

#### List Databases

```bash
dagger call firestore list \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project
```

#### Describe a Database

```bash
dagger call firestore describe \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project \
  --database-id=my-database
```

#### Update Delete Protection

```bash
# Enable delete protection
dagger call firestore update \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project \
  --database-id=my-database \
  --delete-protection=true

# Disable delete protection
dagger call firestore update \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project \
  --database-id=my-database \
  --delete-protection=false
```

#### Delete a Database

```bash
dagger call firestore delete \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project \
  --database-id=my-database
```

**Note:** Use `(default)` as `database-id` to delete the default database. Delete protection must be disabled first.

#### Check if Database Exists

```bash
dagger call firestore exists \
  --credentials=env:GOOGLE_APPLICATION_CREDENTIALS \
  --project-id=my-project \
  --database-id=my-database
```

#### Python Example

```python
from dagger import dag

# Create a new database
await dag.gcp_firebase().firestore().create(
    credentials=credentials,
    project_id="my-project",
    database_id="my-database",
    location="us-central1",
    database_type="firestore-native",
    delete_protection=True,
)

# List all databases
databases = await dag.gcp_firebase().firestore().list(
    credentials=credentials,
    project_id="my-project",
)

# Check if database exists
exists = await dag.gcp_firebase().firestore().exists(
    credentials=credentials,
    project_id="my-project",
    database_id="my-database",
)

# Disable delete protection before deletion
await dag.gcp_firebase().firestore().update(
    credentials=credentials,
    project_id="my-project",
    database_id="my-database",
    delete_protection=False,
)

# Delete the database
await dag.gcp_firebase().firestore().delete(
    credentials=credentials,
    project_id="my-project",
    database_id="my-database",
)
```

---

## Dependencies

- `gcp-auth` - For GCP authentication (used by Firestore)

## License

Apache 2.0
