import { test, expect } from "@playwright/test";

test.describe("Collections Management", () => {
  test("should display user collections", async ({ page }) => {
    await page.goto("/collections");

    // Should show collections sidebar
    await expect(
      page.locator('[data-testid="collections-sidebar"]'),
    ).toBeVisible();

    // Should show default collections
    await expect(page.locator("text=My Collections")).toBeVisible();
    await expect(page.locator("text=Shared with Team")).toBeVisible();

    // Should show prompt list
    await expect(page.locator('[data-testid="prompt-list"]')).toBeVisible();
  });

  test("should create new collection", async ({ page }) => {
    await page.goto("/collections");

    // Click new collection button
    await page.click('[data-testid="new-collection-button"]');

    // Should show create dialog
    await expect(
      page.locator('[data-testid="create-collection-dialog"]'),
    ).toBeVisible();

    // Fill collection details
    await page.fill('[data-testid="collection-name"]', "Test Collection");
    await page.fill(
      '[data-testid="collection-description"]',
      "A test collection",
    );

    // Create collection
    await page.click('[data-testid="create-collection-confirm"]');

    // Should show in sidebar
    await expect(page.locator("text=Test Collection")).toBeVisible();
  });

  test("should search prompts", async ({ page }) => {
    await page.goto("/collections");

    // Use search
    await page.fill('[data-testid="search-input"]', "marketing");

    // Should filter results
    await expect(
      page.locator('[data-testid="prompt-list"] .prompt-item'),
    ).toContainText("marketing");
  });
});
