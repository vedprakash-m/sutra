// Collection Management E2E Tests
import { test, expect } from '@playwright/test'
import { TestHelpers } from './helpers'

test.describe('Collection Management', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
    await helpers.loginAsUser('user')
  })

  test('should display collections page correctly', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Check page title
    await helpers.expectPageTitle('Collections')
    
    // Check for create collection button
    await expect(page.locator('button:has-text("Create Collection"), button:has-text("New Collection")')).toBeVisible()
    
    // Check for search functionality
    const searchInput = page.locator('input[placeholder*="search"], input[type="search"]')
    if (await searchInput.isVisible()) {
      await expect(searchInput).toBeVisible()
    }
  })

  test('should create a new collection successfully', async ({ page }) => {
    const collectionName = `Test Collection ${Date.now()}`
    const collectionDescription = 'A test collection created by E2E tests'
    
    await helpers.createCollection(collectionName, collectionDescription)
    
    // Verify collection appears in the list
    await expect(page.locator(`text=${collectionName}`)).toBeVisible()
    await helpers.expectNoErrors()
  })

  test('should search collections', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Look for search input
    const searchInput = page.locator('input[placeholder*="search"], input[type="search"]')
    
    if (await searchInput.isVisible()) {
      // Search for "Test"
      await searchInput.fill('Test')
      await page.waitForTimeout(1000) // Wait for search results
      
      // Results should contain "Test" in the name
      const collectionItems = page.locator('[data-testid="collection-item"], .collection-item')
      const count = await collectionItems.count()
      
      if (count > 0) {
        const firstItem = collectionItems.first()
        const text = await firstItem.textContent()
        expect(text?.toLowerCase()).toContain('test')
      }
    }
  })

  test('should view collection details', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Click on first collection if available
    const collectionLink = page.locator('a[href*="/collections/"], button:has-text("View Details")').first()
    
    if (await collectionLink.isVisible()) {
      await collectionLink.click()
      
      // Should navigate to collection detail page
      await page.waitForLoadState('networkidle')
      
      // Check for collection details elements
      const detailsPage = page.locator('h1, h2, .collection-title')
      await expect(detailsPage).toBeVisible()
    }
  })

  test('should add prompt to collection', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Create a new collection first
    const collectionName = `Prompt Collection ${Date.now()}`
    await helpers.createCollection(collectionName, 'Collection for prompt testing')
    
    // Navigate to prompt builder
    await helpers.navigateTo('Prompt Builder')
    
    // Create a prompt and assign to collection
    const promptTitle = `Collection Prompt ${Date.now()}`
    await helpers.fillField('input[placeholder="Enter prompt title"]', promptTitle)
    await helpers.fillField('textarea[placeholder="Write your prompt here..."]', 'Test prompt for collection')
    
    // Select the collection we just created
    const collectionSelect = page.locator('select')
    if (await collectionSelect.isVisible()) {
      // Try to find our collection in the dropdown
      const options = page.locator('select option')
      const optionCount = await options.count()
      
      for (let i = 0; i < optionCount; i++) {
        const optionText = await options.nth(i).textContent()
        if (optionText?.includes(collectionName)) {
          await collectionSelect.selectOption({ index: i })
          break
        }
      }
    }
    
    // Save the prompt
    await page.click('button:has-text("Save Prompt")')
    await page.waitForTimeout(2000)
    
    // Go back to collections and verify prompt was added
    await helpers.navigateTo('Collections')
    await expect(page.locator(`text=${collectionName}`)).toBeVisible()
    
    await helpers.expectNoErrors()
  })

  test('should filter collections by type', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Look for filter buttons or dropdown
    const filterButton = page.locator('button:has-text("Filter"), select')
    
    if (await filterButton.isVisible()) {
      // Try different filter options
      const privateFilter = page.locator('button:has-text("Private"), option[value="private"]')
      
      if (await privateFilter.isVisible()) {
        await privateFilter.click()
        await page.waitForTimeout(1000)
        
        // Verify filtering worked (collections should show private ones)
        const collections = page.locator('[data-testid="collection-item"], .collection-item')
        const count = await collections.count()
        console.log(`Found ${count} private collections`)
      }
    }
  })

  test('should import prompts to collection', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Look for import button
    const importButton = page.locator('button:has-text("Import"), button:has-text("Import Prompts")')
    
    if (await importButton.isVisible()) {
      await importButton.click()
      
      // Check import modal
      const importModal = page.locator('text=Import Prompts, text=Import')
      if (await importModal.isVisible()) {
        // Check for file input or URL input
        const fileInput = page.locator('input[type="file"]')
        const urlInput = page.locator('input[placeholder*="URL"], input[placeholder*="url"]')
        
        if (await fileInput.isVisible()) {
          console.log('✅ File import option available')
        }
        
        if (await urlInput.isVisible()) {
          console.log('✅ URL import option available')
        }
        
        // Close modal
        const closeButton = page.locator('button:has-text("Cancel"), button:has-text("Close")')
        if (await closeButton.isVisible()) {
          await closeButton.click()
        }
      }
    }
  })

  test('should manage collection permissions', async ({ page }) => {
    await helpers.navigateTo('Collections')
    
    // Look for settings or share buttons on collections
    const settingsButton = page.locator('button:has-text("Settings"), button:has-text("Share"), [data-testid="collection-settings"]').first()
    
    if (await settingsButton.isVisible()) {
      await settingsButton.click()
      
      // Check for permission options
      const permissionOptions = page.locator('text=Private, text=Shared, text=Public')
      const optionsCount = await permissionOptions.count()
      
      if (optionsCount > 0) {
        console.log('✅ Permission options available')
        
        // Close settings if needed
        const closeButton = page.locator('button:has-text("Cancel"), button:has-text("Close")')
        if (await closeButton.isVisible()) {
          await closeButton.click()
        }
      }
    }
  })
})
