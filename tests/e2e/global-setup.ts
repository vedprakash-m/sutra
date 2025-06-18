// Global setup for Playwright tests
import { chromium } from "@playwright/test";

async function globalSetup() {
  console.log("🚀 Starting global setup for E2E tests...");

  // Wait for services to be ready
  await waitForServices();

  // Initialize test database with seed data
  await initializeTestData();

  console.log("✅ Global setup completed successfully");
}

async function waitForServices() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Wait for frontend to be ready
  console.log("⏳ Waiting for frontend to be ready...");
  for (let i = 0; i < 30; i++) {
    try {
      await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
      console.log("✅ Frontend is ready");
      break;
    } catch (error) {
      if (i === 29) {
        throw new Error("Frontend failed to start after 30 attempts");
      }
      await page.waitForTimeout(2000);
    }
  }

  // Wait for API to be ready
  console.log("⏳ Waiting for API to be ready...");
  for (let i = 0; i < 30; i++) {
    try {
      const response = await page.request.get(
        "http://localhost:7071/api/health",
      );
      if (response.ok()) {
        console.log("✅ API is ready");
        break;
      }
    } catch (error) {
      if (i === 29) {
        console.log("⚠️ API health check failed, proceeding anyway...");
        break;
      }
      await page.waitForTimeout(2000);
    }
  }

  await browser.close();
}

async function initializeTestData() {
  console.log("📊 Initializing test data...");

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Clear existing test data using the admin endpoint
    try {
      console.log("🧹 Clearing existing test data...");
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
          "✅ Test data cleared successfully:",
          resetData.containers_reset?.length || 0,
          "containers",
        );
      } else {
        console.log(
          "⚠️ Could not clear existing data, status:",
          resetResponse.status(),
        );
      }
    } catch (error) {
      console.log("⚠️ Could not clear existing data, proceeding...", error);
    }

    // Seed fresh test data using the admin endpoint
    try {
      console.log("🌱 Seeding fresh test data...");
      const seedResponse = await page.request.post(
        "http://localhost:7071/api/admin/test-data/seed",
        {
          data: {
            includeUsers: true,
            includeCollections: true,
            includePrompts: true,
            includeAdminSettings: true,
          },
          headers: {
            "Content-Type": "application/json",
            "x-test-auth": "admin",
          },
        },
      );

      if (seedResponse.ok()) {
        const seedData = await seedResponse.json();
        console.log(
          "✅ Test data seeded successfully:",
          seedData.data_created?.length || 0,
          "items created",
        );
      } else {
        console.log(
          "⚠️ Could not seed test data, status:",
          seedResponse.status(),
        );
        const errorText = await seedResponse.text();
        console.log("Error details:", errorText);
      }
    } catch (error) {
      console.log("⚠️ Could not seed test data:", error);
    }

    // Wait a moment for data consistency
    await page.waitForTimeout(1000);

    console.log("✅ Test data initialization completed");
  } catch (error) {
    console.error("❌ Error during test data initialization:", error);
  } finally {
    await browser.close();
  }
}

export default globalSetup;
