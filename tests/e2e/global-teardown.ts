// Global teardown for Playwright tests
import { chromium } from "@playwright/test";

async function globalTeardown() {
  console.log("🧹 Starting global teardown for E2E tests...");

  // Clean up test data
  await cleanupTestData();

  console.log("✅ Global teardown completed successfully");
}

async function cleanupTestData() {
  console.log("🗑️ Cleaning up test data...");

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Call admin cleanup endpoint to reset test database
    const resetResponse = await page.request.post(
      "http://localhost:7071/api/admin/test-data/reset",
      {
        headers: {
          "Content-Type": "application/json",
          "x-test-auth": "admin",
        },
      },
    );

    if (resetResponse.ok()) {
      const resetData = await resetResponse.json();
      console.log(
        "✅ Test data cleanup completed:",
        resetData.containers_reset?.length || 0,
        "containers cleaned",
      );
    } else {
      console.log(
        "⚠️ Could not clean up test data, status:",
        resetResponse.status(),
      );
    }
  } catch (error) {
    console.log("⚠️ Could not clean up test data:", error);
  } finally {
    await browser.close();
  }
}

export default globalTeardown;
