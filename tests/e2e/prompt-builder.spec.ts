import { test, expect } from "@playwright/test";

test.describe("Prompt Builder", () => {
  test("should create a new prompt", async ({ page }) => {
    await page.goto("/prompts/new");

    // Fill in prompt details
    await page.fill(
      '[data-testid="intention-input"]',
      "Write a marketing email",
    );
    await page.selectOption('[data-testid="tone-select"]', "persuasive");
    await page.fill(
      '[data-testid="prompt-text"]',
      "Act as a marketing expert and write a persuasive email for {{product_name}}",
    );

    // Select LLMs
    await page.check('[data-testid="llm-openai"]');
    await page.check('[data-testid="llm-gemini"]');

    // Click generate
    await page.click('[data-testid="generate-button"]');

    // Should show loading state
    await expect(
      page.locator('[data-testid="loading-indicator"]'),
    ).toBeVisible();

    // Should show outputs (mock response)
    await expect(page.locator('[data-testid="llm-output-1"]')).toBeVisible();
  });

  test("should save prompt to collection", async ({ page }) => {
    await page.goto("/prompts/new");

    // Create a prompt
    await page.fill('[data-testid="intention-input"]', "Test prompt");
    await page.fill('[data-testid="prompt-text"]', "This is a test prompt");

    // Save to collection
    await page.click('[data-testid="save-button"]');

    // Should show save dialog
    await expect(page.locator('[data-testid="save-dialog"]')).toBeVisible();

    // Select collection and save
    await page.selectOption(
      '[data-testid="collection-select"]',
      "My Collection",
    );
    await page.click('[data-testid="confirm-save"]');

    // Should show success message
    await expect(page.locator("text=Prompt saved successfully")).toBeVisible();
  });
});
