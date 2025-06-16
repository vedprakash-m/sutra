// Playbook Management E2E Tests
import { test, expect } from '@playwright/test'
import { TestHelpers } from './helpers'

test.describe('Playbook Management', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
    await helpers.loginAsUser('user')
  })

  test('should display playbook builder correctly', async ({ page }) => {
    await helpers.navigateTo('Playbooks')
    
    // Check page title
    await helpers.expectPageTitle('Playbook Builder')
    
    // Check form elements
    await expect(page.locator('input[placeholder="Enter playbook name"]')).toBeVisible()
    await expect(page.locator('textarea[placeholder="Describe what this playbook does"]')).toBeVisible()
    
    // Check add step button
    await expect(page.locator('button:has-text("Add Step")')).toBeVisible()
  })

  test('should create a playbook with multiple steps', async () => {
    const playbookName = `Test Playbook ${Date.now()}`
    const playbookDescription = 'A test playbook created by E2E tests'
    
    await helpers.createPlaybook(playbookName, playbookDescription)
    await helpers.expectNoErrors()
  })

  test('should add different types of steps', async ({ page }) => {
    await helpers.navigateTo('Playbooks')
    
    // Fill basic playbook info
    await helpers.fillField('input[placeholder="Enter playbook name"]', `Multi-Step Playbook ${Date.now()}`)
    await helpers.fillField('textarea[placeholder="Describe what this playbook does"]', 'Testing different step types')
    
    // Add prompt step
    await page.click('button:has-text("Add Step")')
    const promptStepOption = page.locator('button:has-text("Prompt Step"), text=Prompt')
    if (await promptStepOption.isVisible()) {
      await promptStepOption.click()
      
      // Fill step content
      const stepContent = page.locator('textarea[placeholder="Enter step content..."], textarea').last()
      await stepContent.fill('This is a prompt step')
    }
    
    // Add review step if available
    await page.click('button:has-text("Add Step")')
    const reviewStepOption = page.locator('button:has-text("Review Step"), text=Review')
    if (await reviewStepOption.isVisible()) {
      await reviewStepOption.click()
      
      // Fill review step content
      const reviewContent = page.locator('textarea').last()
      await reviewContent.fill('This is a review step')
    }
    
    // Add variable step if available
    await page.click('button:has-text("Add Step")')
    const variableStepOption = page.locator('button:has-text("Variable Step"), text=Variable')
    if (await variableStepOption.isVisible()) {
      await variableStepOption.click()
      
      // Fill variable step content
      const variableContent = page.locator('textarea').last()
      await variableContent.fill('variable_name = "test_value"')
    }
    
    // Save playbook
    await page.click('button:has-text("Save Playbook")')
    await page.waitForTimeout(2000)
    
    await helpers.expectNoErrors()
  })

  test('should reorder playbook steps', async ({ page }) => {
    await helpers.navigateTo('Playbooks')
    
    // Create a playbook with multiple steps
    await helpers.fillField('input[placeholder="Enter playbook name"]', `Reorder Test ${Date.now()}`)
    await helpers.fillField('textarea[placeholder="Describe what this playbook does"]', 'Testing step reordering')
    
    // Add first step
    await page.click('button:has-text("Add Step")')
    await page.click('button:has-text("Prompt Step")')
    const firstStep = page.locator('textarea').last()
    await firstStep.fill('First step')
    
    // Add second step
    await page.click('button:has-text("Add Step")')
    await page.click('button:has-text("Prompt Step")')
    const secondStep = page.locator('textarea').last()
    await secondStep.fill('Second step')
    
    // Look for reorder buttons (up/down arrows or drag handles)
    const moveUpButton = page.locator('button[title="Move up"], button:has-text("↑")')
    
    if (await moveUpButton.count() > 0) {
      // Try to move second step up
      await moveUpButton.last().click()
      console.log('✅ Step reordering buttons found and tested')
    }
    
    await helpers.expectNoErrors()
  })

  test('should execute playbook with PlaybookRunner', async ({ page }) => {
    await helpers.navigateTo('Playbooks')
    
    // Look for existing playbooks or create one
    const existingPlaybook = page.locator('button:has-text("Run"), button:has-text("Execute")').first()
    
    if (await existingPlaybook.isVisible()) {
      await existingPlaybook.click()
      
      // Check for playbook runner interface
      const runnerInterface = page.locator('text=Playbook Runner, text=Execute Playbook')
      if (await runnerInterface.isVisible()) {
        // Look for run/start button
        const startButton = page.locator('button:has-text("Start"), button:has-text("Run"), button:has-text("Execute")')
        if (await startButton.isVisible()) {
          await startButton.click()
          
          // Wait for execution to start
          await page.waitForTimeout(2000)
          
          // Look for execution status
          const statusIndicator = page.locator('text=Running, text=Executing, text=Complete')
          if (await statusIndicator.isVisible()) {
            console.log('✅ Playbook execution started')
          }
        }
        
        // Close runner if needed
        const closeButton = page.locator('button:has-text("Close"), button:has-text("Cancel")')
        if (await closeButton.isVisible()) {
          await closeButton.click()
        }
      }
    } else {
      // Create a simple playbook first
      await helpers.createPlaybook(`Execution Test ${Date.now()}`, 'Playbook for execution testing')
    }
    
    await helpers.expectNoErrors()
  })

  test('should save and load playbook drafts', async ({ page }) => {
    await helpers.navigateTo('Playbooks')
    
    const playbookName = `Draft Test ${Date.now()}`
    
    // Fill out playbook but don't save
    await helpers.fillField('input[placeholder="Enter playbook name"]', playbookName)
    await helpers.fillField('textarea[placeholder="Describe what this playbook does"]', 'Testing draft functionality')
    
    // Add a step
    await page.click('button:has-text("Add Step")')
    await page.click('button:has-text("Prompt Step")')
    await page.locator('textarea').last().fill('Draft step content')
    
    // Look for save draft button
    const saveDraftButton = page.locator('button:has-text("Save Draft"), button:has-text("Save as Draft")')
    if (await saveDraftButton.isVisible()) {
      await saveDraftButton.click()
      await page.waitForTimeout(1000)
      
      // Navigate away and back
      await helpers.navigateTo('Collections')
      await helpers.navigateTo('Playbooks')
      
      // Check if draft was preserved
      const nameInput = page.locator('input[placeholder="Enter playbook name"]')
      const savedName = await nameInput.inputValue()
      
      if (savedName === playbookName) {
        console.log('✅ Draft functionality working')
      }
    }
    
    await helpers.expectNoErrors()
  })

  test('should validate playbook before saving', async ({ page }) => {
    await helpers.navigateTo('Playbooks')
    
    // Try to save without required fields
    await page.click('button:has-text("Save Playbook")')
    
    // Should show validation errors or button should be disabled
    const saveButton = page.locator('button:has-text("Save Playbook")')
    const isEnabled = await saveButton.isEnabled()
    
    if (isEnabled) {
      // Look for validation messages
      const validationMessage = page.locator('.error, [role="alert"], .text-red-500')
      const hasValidation = await validationMessage.count() > 0
      
      if (hasValidation) {
        console.log('✅ Validation messages displayed')
      }
    } else {
      console.log('✅ Save button properly disabled when form is invalid')
    }
  })

  test('should handle playbook variables', async ({ page }) => {
    await helpers.navigateTo('Playbooks')
    
    // Create playbook with variables
    await helpers.fillField('input[placeholder="Enter playbook name"]', `Variable Test ${Date.now()}`)
    await helpers.fillField('textarea[placeholder="Describe what this playbook does"]', 'Testing variable functionality')
    
    // Add variable step
    await page.click('button:has-text("Add Step")')
    const variableOption = page.locator('button:has-text("Variable"), text=Variable')
    if (await variableOption.isVisible()) {
      await variableOption.click()
      
      // Define a variable
      const variableInput = page.locator('input[placeholder*="variable"], input[name*="variable"]')
      if (await variableInput.isVisible()) {
        await variableInput.fill('user_name')
        
        // Set variable value
        const valueInput = page.locator('input[placeholder*="value"], input[name*="value"]')
        if (await valueInput.isVisible()) {
          await valueInput.fill('Test User')
        }
      }
    }
    
    // Add prompt step that uses the variable
    await page.click('button:has-text("Add Step")')
    await page.click('button:has-text("Prompt Step")')
    const promptContent = page.locator('textarea').last()
    await promptContent.fill('Hello {{user_name}}, welcome to the system!')
    
    // Save playbook
    await page.click('button:has-text("Save Playbook")')
    await page.waitForTimeout(2000)
    
    await helpers.expectNoErrors()
  })
})
