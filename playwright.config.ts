import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for E2E testing
 * Configured for single-worker mode to ensure test isolation
 * with global setup/teardown for data management
 */
export default defineConfig({
  // Test directory
  testDir: "./tests/e2e",

  // Global setup and teardown
  globalSetup: require.resolve("./tests/e2e/global-setup.ts"),
  globalTeardown: require.resolve("./tests/e2e/global-teardown.ts"),

  // Run tests in files in parallel but use only one worker
  // This ensures test data isolation while maintaining speed
  fullyParallel: false,
  workers: 1,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Reporter configuration
  reporter: [
    ["html", { outputFolder: "playwright-report" }],
    ["json", { outputFile: "test-results.json" }],
    ["list"],
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL for tests
    baseURL: "http://localhost:3000",

    // Collect trace when retrying the failed test
    trace: "on-first-retry",

    // Record video on failure
    video: "retain-on-failure",

    // Take screenshot on failure
    screenshot: "only-on-failure",

    // Global test timeout
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // Configure projects for major browsers and devices
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },

    // Mobile devices
    {
      name: "Mobile Chrome",
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "Mobile Safari",
      use: { ...devices["iPhone 12"] },
    },
  ],

  // Run your local dev server before starting the tests
  webServer: {
    command: "docker-compose up -d --build",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // 2 minutes for Docker services to start
  },

  // Test timeout
  timeout: 30000,

  // Expect timeout for assertions
  expect: {
    timeout: 5000,
  },

  // Output directory for test artifacts
  outputDir: "test-results/",
});
