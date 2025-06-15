import { test, expect } from '@playwright/test'

test.describe('Sutra Application', () => {
  test('should load the login page and authenticate', async ({ page }) => {
    await page.goto('/')
    
    // Should see login page initially
    await expect(page.locator('h2')).toContainText('Sign in to Sutra')
    
    // Select user radio button and login
    await page.click('text=Regular User')
    await page.click('button:has-text("Sign in (Development Mode)")')
    
    // Should navigate to dashboard
    await expect(page.locator('h1').filter({ hasText: 'Welcome back' })).toBeVisible()
    await expect(page.locator('nav')).toContainText('Sutra')
  })

  test('should navigate between main pages', async ({ page }) => {
    await page.goto('/')
    
    // Login first
    await page.click('text=Regular User')
    await page.click('button:has-text("Sign in (Development Mode)")')
    await expect(page.locator('h1').filter({ hasText: 'Welcome back' })).toBeVisible()
    
    // Navigate to Prompt Builder
    await page.click('nav a:has-text("Prompt Builder")')
    await expect(page.locator('h1')).toContainText('Prompt Builder')
    
    // Navigate to Collections
    await page.click('nav a:has-text("Collections")')
    await expect(page.locator('h1')).toContainText('Collections')
    
    // Navigate to Playbooks
    await page.click('nav a:has-text("Playbooks")')
    await expect(page.locator('h1')).toContainText('Playbook Builder')
    
    // Navigate to Integrations
    await page.click('nav a:has-text("Integrations")')
    await expect(page.locator('h1')).toContainText('Integrations')
  })

  test('should show admin panel for admin users', async ({ page }) => {
    await page.goto('/')
    
    // Login as admin
    await page.click('text=Administrator')
    await page.click('button:has-text("Sign in (Development Mode)")')
    await expect(page.locator('h1').filter({ hasText: 'Welcome back' })).toBeVisible()
    
    // Should see admin link in nav
    await expect(page.locator('nav a:has-text("Admin")')).toBeVisible()
    
    // Navigate to admin panel
    await page.click('nav a:has-text("Admin")')
    await expect(page.locator('h1')).toContainText('Admin Panel')
    
    // Should see admin tabs
    await expect(page.locator('text=Overview')).toBeVisible()
    await expect(page.locator('text=LLM Settings')).toBeVisible()
    await expect(page.locator('text=System Health')).toBeVisible()
  })

  test('should create a prompt', async ({ page }) => {
    await page.goto('/')
    
    // Login and navigate to prompt builder
    await page.click('text=Regular User')
    await page.click('button:has-text("Sign in (Development Mode)")')
    await page.click('nav a:has-text("Prompt Builder")')
    
    // Fill out prompt form
    await page.fill('input[placeholder="Enter prompt title"]', 'Test Prompt')
    await page.fill('textarea[placeholder="Describe what this prompt does"]', 'This is a test prompt')
    await page.fill('textarea[placeholder="Write your prompt here..."]', 'Hello, world! This is a test prompt.')
    
    // Select LLMs (OpenAI should be selected by default)
    await expect(page.locator('input[type="checkbox"]').first()).toBeChecked()
    
    // Save button should be enabled
    await expect(page.locator('button:has-text("Save Prompt")')).toBeEnabled()
  })
})
