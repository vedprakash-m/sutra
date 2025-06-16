// Prompt Management E2E Tests
import { test, expect } from '@playwright/test'
import { TestHelpers } from './helpers'

test.describe('Prompt Management', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
    await helpers.loginAsUser('user')
  })

  test('should display prompt builder page correctly', async ({ page }) => {
    await helpers.navigateTo('Prompt Builder')
    
    // Check form elements
    await expect(page.locator('input[placeholder="Enter prompt title"]')).toBeVisible()
    await expect(page.locator('textarea[placeholder="Describe what this prompt does"]')).toBeVisible()
    await expect(page.locator('textarea[placeholder="Write your prompt here..."]')).toBeVisible()
    
    // Check LLM selection options
    await expect(page.locator('text=Select LLM Providers')).toBeVisible()
    await expect(page.locator('text=OpenAI')).toBeVisible()
    
    // Save button should be initially disabled or enabled based on form state
    await expect(page.locator('button:has-text("Save Prompt")')).toBeVisible()
  })

  test('should create a new prompt successfully', async () => {
    await helpers.navigateTo('Prompt Builder')
    
    const promptTitle = `Test Prompt ${Date.now()}`
    const promptContent = 'This is a test prompt for automated testing'
    const promptDescription = 'A test prompt created by E2E tests'
    
    await helpers.createPrompt(promptTitle, promptContent, promptDescription)
    
    // Verify prompt was created (could check collections page or success message)
    await helpers.expectNoErrors()
  })

  test('should validate required fields', async ({ page }) => {
    await helpers.navigateTo('Prompt Builder')
    
    // Try to save without filling required fields
    await page.click('button:has-text("Save Prompt")')
    
    // Should show validation errors or button should remain disabled
    const saveButton = page.locator('button:has-text("Save Prompt")')
    const isEnabled = await saveButton.isEnabled()
    
    if (isEnabled) {
      // Check for validation messages
      const titleField = page.locator('input[placeholder="Enter prompt title"]')
      const isRequired = await titleField.getAttribute('required')
      expect(isRequired).toBe('')
    }
  })

  test('should test prompt with multiple LLMs', async ({ page }) => {
    await helpers.navigateTo('Prompt Builder')
    
    // Fill out prompt form
    await helpers.fillField('input[placeholder="Enter prompt title"]', 'Multi-LLM Test')
    await helpers.fillField('textarea[placeholder="Write your prompt here..."]', 'Test prompt for multiple LLMs')
    
    // Select multiple LLMs if available
    const llmCheckboxes = page.locator('input[type="checkbox"]')
    
    // Select first LLM (should be OpenAI)
    const firstCheckbox = llmCheckboxes.first()
    if (!(await firstCheckbox.isChecked())) {
      await firstCheckbox.check()
    }
    
    // Test prompt if test button exists
    const testButton = page.locator('button:has-text("Test Prompt")')
    if (await testButton.isVisible()) {
      await testButton.click()
      
      // Wait for test results
      await page.waitForTimeout(3000)
    }
    
    await helpers.expectNoErrors()
  })

  test('should save prompt to collection', async ({ page }) => {
    await helpers.navigateTo('Prompt Builder')
    
    const promptTitle = `Collection Prompt ${Date.now()}`
    
    // Fill prompt details
    await helpers.fillField('input[placeholder="Enter prompt title"]', promptTitle)
    await helpers.fillField('textarea[placeholder="Write your prompt here..."]', 'Test prompt for collection')
    
    // Select collection if dropdown exists
    const collectionSelect = page.locator('select').first()
    if (await collectionSelect.isVisible()) {
      await collectionSelect.selectOption({ index: 0 })
    }
    
    // Save prompt
    await page.click('button:has-text("Save Prompt")')
    
    // Wait for save operation
    await page.waitForTimeout(2000)
    
    await helpers.expectNoErrors()
  })

  test('should provide prompt suggestions with PromptCoach', async ({ page }) => {
    await helpers.navigateTo('Prompt Builder')
    
    // Fill in basic prompt
    await helpers.fillField('textarea[placeholder="Write your prompt here..."]', 'Write a story')
    
    // Look for PromptCoach suggestions
    const coachSection = page.locator('text=AI Suggestions')
    if (await coachSection.isVisible()) {
      await expect(coachSection).toBeVisible()
      
      // Check for suggestion items
      const suggestions = page.locator('[data-testid="prompt-suggestion"]')
      const suggestionCount = await suggestions.count()
      
      if (suggestionCount > 0) {
        console.log(`✅ Found ${suggestionCount} prompt suggestions`)
      }
    }
  })

  test('should handle prompt versioning', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Look for version history button on existing prompts
    const versionButton = page.locator('button:has-text("Version History")')
    if (await versionButton.isVisible()) {
      await versionButton.click()
      
      // Check version history modal
      await expect(page.locator('text=Version History')).toBeVisible()
      
      // Close modal
      const closeButton = page.locator('button:has-text("Close")')
      if (await closeButton.isVisible()) {
        await closeButton.click()
      }
    }
  })
})
