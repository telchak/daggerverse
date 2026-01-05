"""
Test script: Seed sample data into Firestore using Python

This script is used by the gcp-firebase module tests to verify
that the scripts().python() function works correctly.

Environment variables:
- FIRESTORE_DATABASE_ID: The database ID to use (optional, defaults to "(default)")
- GOOGLE_APPLICATION_CREDENTIALS: Path to GCP credentials (set by Dagger)
"""

import json
import os
from datetime import datetime

from google.cloud import firestore

database_id = os.environ.get("FIRESTORE_DATABASE_ID", "(default)")

db = firestore.Client(database=database_id)


def seed_data() -> None:
    """Seed test data into Firestore."""
    print(f"Seeding test data to Firestore database: {database_id}")

    collection_ref = db.collection("dagger-test-collection-python")
    batch = db.batch()

    # Create test documents
    test_docs = [
        {"name": "python-item-1", "value": 1000, "tags": ["dagger", "python"], "source": "python"},
        {"name": "python-item-2", "value": 2000, "tags": ["dagger", "test"], "source": "python"},
        {"name": "python-item-3", "value": 3000, "tags": ["dagger", "ci"], "source": "python"},
    ]

    for doc in test_docs:
        doc_ref = collection_ref.document(doc["name"])
        batch.set(doc_ref, {
            **doc,
            "createdAt": firestore.SERVER_TIMESTAMP,
        })
        print(f"  Adding document: {doc['name']}")

    batch.commit()
    print(f"Successfully seeded {len(test_docs)} documents to Firestore!")

    # Output summary for test verification
    print(json.dumps({
        "status": "success",
        "database": database_id,
        "collection": "dagger-test-collection-python",
        "documentCount": len(test_docs),
        "documents": [d["name"] for d in test_docs],
    }))


if __name__ == "__main__":
    seed_data()
