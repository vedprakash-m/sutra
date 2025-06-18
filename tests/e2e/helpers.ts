// Test helpers for E2E tests
import { Page, expect } from "@playwright/test";

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Login as a test user
   */
  async loginAsUser(userType: "user" | "admin" = "user") {
    await this.page.goto("/");

    // Wait for login page to load
    await expect(this.page.locator("h2")).toContainText("Sign in to Sutra");

    // Select user type
    const radioButton = userType === "admin" ? "Admin User" : "Regular User";
    await this.page.click(`text=${radioButton}`);

    // Click login button
    await this.page.click('button:has-text("Sign in (Development Mode)")');

    // Wait for dashboard to load
    await expect(
      this.page.locator("h1").filter({ hasText: "Welcome back" }),
    ).toBeVisible({ timeout: 10000 });

    console.log(`✅ Logged in as ${userType}`);
  }

  /**
   * Logout current user
   */
  async logout() {
    await this.page.click('button:has-text("Sign Out")');
    await expect(this.page.locator("h2")).toContainText("Sign in to Sutra");
    console.log("✅ Logged out successfully");
  }

  /**
   * Navigate to a specific page
   */
  async navigateTo(pageName: string) {
    await this.page.click(`nav a:has-text("${pageName}")`);
    await this.page.waitForLoadState("networkidle");
    console.log(`✅ Navigated to ${pageName}`);
  }

  /**
   * Create a new collection
   */
  async createCollection(name: string, description: string) {
    await this.navigateTo("Collections");

    // Click create button
    await this.page.click('button:has-text("Create Collection")');

    // Fill out form
    await this.page.fill('input[placeholder*="collection name"]', name);
    await this.page.fill('textarea[placeholder*="description"]', description);

    // Submit form
    await this.page.click('button:has-text("Create")');

    // Wait for collection to appear
    await expect(this.page.locator(`text=${name}`)).toBeVisible();
    console.log(`✅ Created collection: ${name}`);
  }

  /**
   * Create a new prompt
   */
  async createPrompt(title: string, content: string, description?: string) {
    await this.navigateTo("Prompt Builder");

    // Fill out prompt form
    await this.page.fill('input[placeholder="Enter prompt title"]', title);
    if (description) {
      await this.page.fill(
        'textarea[placeholder="Describe what this prompt does"]',
        description,
      );
    }
    await this.page.fill(
      'textarea[placeholder="Write your prompt here..."]',
      content,
    );

    // Ensure OpenAI is selected (should be by default)
    const openaiCheckbox = this.page.locator('input[type="checkbox"]').first();
    if (!(await openaiCheckbox.isChecked())) {
      await openaiCheckbox.check();
    }

    // Save prompt
    await this.page.click('button:has-text("Save Prompt")');

    // Wait for success message or redirect
    await this.page.waitForTimeout(2000);
    console.log(`✅ Created prompt: ${title}`);
  }

  /**
   * Create a new playbook
   */
  async createPlaybook(name: string, description: string) {
    await this.navigateTo("Playbooks");

    // Fill out playbook form
    await this.page.fill('input[placeholder="Enter playbook name"]', name);
    await this.page.fill(
      'textarea[placeholder="Describe what this playbook does"]',
      description,
    );

    // Add a step
    await this.page.click('button:has-text("Add Step")');
    await this.page.click('button:has-text("Prompt Step")');

    // Fill step content
    await this.page.fill(
      'textarea[placeholder="Enter step content..."]',
      "This is a test step",
    );

    // Save playbook
    await this.page.click('button:has-text("Save Playbook")');

    await this.page.waitForTimeout(2000);
    console.log(`✅ Created playbook: ${name}`);
  }

  /**
   * Wait for element to be visible with custom timeout
   */
  async waitForElement(selector: string, timeout: number = 10000) {
    await this.page.waitForSelector(selector, { timeout });
  }

  /**
   * Take screenshot for debugging
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({
      path: `test-results/screenshots/${name}.png`,
    });
    console.log(`📸 Screenshot saved: ${name}.png`);
  }

  /**
   * Check if user is on the expected page
   */
  async expectPageTitle(title: string) {
    await expect(this.page.locator("h1")).toContainText(title);
  }

  /**
   * Check for error messages
   */
  async expectNoErrors() {
    const errorElements = this.page.locator(
      '[role="alert"], .error, .text-red-500',
    );
    const count = await errorElements.count();
    if (count > 0) {
      const errorText = await errorElements.first().textContent();
      throw new Error(`Unexpected error found: ${errorText}`);
    }
  }

  /**
   * Fill form field with validation
   */
  async fillField(selector: string, value: string) {
    await this.page.fill(selector, value);
    // Verify the field was filled
    const fieldValue = await this.page.inputValue(selector);
    expect(fieldValue).toBe(value);
  }

  /**
   * Clear test data during test execution
   */
  async clearTestData() {
    try {
      await this.page.request.post(
        "http://localhost:7071/api/admin/reset-test-data",
        {
          headers: {
            "Content-Type": "application/json",
            "x-test-auth": "admin",
          },
        },
      );
      console.log("🧹 Test data cleared");
    } catch (error) {
      console.log("⚠️ Could not clear test data:", error);
    }
  }
}
