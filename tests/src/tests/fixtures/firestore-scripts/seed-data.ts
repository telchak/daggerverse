/**
 * Test script: Seed sample data into Firestore
 *
 * This script is used by the gcp-firebase module tests to verify
 * that the scripts().node() function works correctly.
 *
 * Environment variables:
 * - FIRESTORE_DATABASE_ID: The database ID to use (optional, defaults to "(default)")
 * - GOOGLE_APPLICATION_CREDENTIALS: Path to GCP credentials (set by Dagger)
 */

import { Firestore, FieldValue } from "@google-cloud/firestore";

const databaseId = process.env.FIRESTORE_DATABASE_ID || "(default)";

const db = new Firestore({
  databaseId: databaseId,
});

interface TestDocument {
  name: string;
  value: number;
  tags: string[];
  createdAt: FirebaseFirestore.FieldValue;
  source: string;
}

async function seedData(): Promise<void> {
  console.log(`Seeding test data to Firestore database: ${databaseId}`);

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

seedData()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Error seeding data:", error);
    process.exit(1);
  });
