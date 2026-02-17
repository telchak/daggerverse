/**
 * Test script: Seed sample data into Firestore
 *
 * This script is used by the gcp-firebase module tests to verify
 * that the scripts().node() function works correctly.
 *
 * Environment variables:
 * - FIRESTORE_DATABASE_ID: The database ID to use (optional, defaults to "(default)")
 * - GOOGLE_ACCESS_TOKEN: Access token for authentication (optional, for CI/CD)
 * - GOOGLE_CLOUD_PROJECT: Project ID (required when using access token)
 * - GOOGLE_APPLICATION_CREDENTIALS: Path to GCP credentials (set by Dagger)
 */

import { Firestore, FieldValue } from "@google-cloud/firestore";
import { OAuth2Client } from "google-auth-library";

const databaseId = process.env.FIRESTORE_DATABASE_ID || "(default)";
const accessToken = process.env.GOOGLE_ACCESS_TOKEN;
const projectId = process.env.GOOGLE_CLOUD_PROJECT;

// Create Firestore client with appropriate authentication
async function createFirestoreClient(): Promise<Firestore> {
  if (accessToken) {
    // Use explicit access token (for CI/CD with OIDC)
    const oauth2Client = new OAuth2Client();
    oauth2Client.setCredentials({ access_token: accessToken });

    return new Firestore({
      projectId: projectId,
      databaseId: databaseId,
      authClient: oauth2Client as any,
    });
  }

  // Use Application Default Credentials
  return new Firestore({
    databaseId: databaseId,
  });
}

interface TestDocument {
  name: string;
  value: number;
  tags: string[];
  createdAt: FirebaseFirestore.FieldValue;
  source: string;
}

async function seedData(): Promise<void> {
  console.log(`Seeding test data to Firestore database: ${databaseId}`);

  const db = await createFirestoreClient();
  const collectionRef = db.collection("dagger-test-collection");
  const batch = db.batch();

  // Create test documents
  const testDocs: Omit<TestDocument, "createdAt">[] = [
    { name: "test-item-1", value: 100, tags: ["dagger", "test"], source: "typescript" },
    { name: "test-item-2", value: 200, tags: ["dagger", "ci"], source: "typescript" },
    { name: "test-item-3", value: 300, tags: ["dagger", "automated"], source: "typescript" },
  ];

  for (const doc of testDocs) {
    const docRef = collectionRef.doc(doc.name);
    batch.set(docRef, {
      ...doc,
      createdAt: FieldValue.serverTimestamp(),
    });
    console.log(`  Adding document: ${doc.name}`);
  }

  await batch.commit();
  console.log(`Successfully seeded ${testDocs.length} documents to Firestore!`);

  // Output summary for test verification
  console.log(JSON.stringify({
    status: "success",
    database: databaseId,
    collection: "dagger-test-collection",
    documentCount: testDocs.length,
    documents: testDocs.map((d) => d.name),
  }));
}

try {
  await seedData();
  process.exit(0);
} catch (error) {
  console.error("Error seeding data:", error);
  process.exit(1);
}
