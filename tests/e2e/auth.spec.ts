// Authentication and User Management E2E Tests
import { test, expect } from '@playwright/test'
import { TestHelpers } from './helpers'

test.describe('Authentication and User Management', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
  })

  test('should display login page correctly', async ({ page }) => {
    await page.goto('/')
    
    // Check login page elements
    await expect(page.locator('h2')).toContainText('Sign in to Sutra')
    await expect(page.locator('text=Regular User')).toBeVisible()
    await expect(page.locator('text=Admin User')).toBeVisible()
    await expect(page.locator('button:has-text("Sign in (Development Mode)")')).toBeVisible()
  })

  test('should allow regular user login and access dashboard', async ({ page }) => {
    await helpers.loginAsUser('user')
    
    // Verify dashboard content
    await helpers.expectPageTitle('Welcome back')
    await expect(page.locator('nav')).toContainText('Sutra')
    
    // Check navigation items for regular user
    await expect(page.locator('nav a:has-text("Prompt Builder")')).toBeVisible()
    await expect(page.locator('nav a:has-text("Collections")')).toBeVisible()
    await expect(page.locator('nav a:has-text("Playbooks")')).toBeVisible()
    await expect(page.locator('nav a:has-text("Integrations")')).toBeVisible()
    
    // Admin link should not be visible for regular user
    await expect(page.locator('nav a:has-text("Admin")')).not.toBeVisible()
  })

  test('should allow admin user login and access admin panel', async ({ page }) => {
    await helpers.loginAsUser('admin')
    
    // Verify dashboard content
    await helpers.expectPageTitle('Welcome back')
    
    // Check that admin has access to admin panel
    await expect(page.locator('nav a:has-text("Admin")')).toBeVisible()
    
    // Navigate to admin panel
    await helpers.navigateTo('Admin')
    await helpers.expectPageTitle('Admin Panel')
    
    // Check admin panel tabs
    await expect(page.locator('text=Overview')).toBeVisible()
    await expect(page.locator('text=LLM Settings')).toBeVisible()
    await expect(page.locator('text=System Health')).toBeVisible()
  })

  test('should handle logout correctly', async ({ page }) => {
    await helpers.loginAsUser('user')
    
    // Verify logged in
    await helpers.expectPageTitle('Welcome back')
    
    // Logout
    await helpers.logout()
    
    // Should return to login page
    await expect(page.locator('h2')).toContainText('Sign in to Sutra')
  })

  test('should maintain user session across page navigation', async ({ page }) => {
    await helpers.loginAsUser('user')
    
    // Navigate through different pages
    await helpers.navigateTo('Prompt Builder')
    await helpers.expectPageTitle('Prompt Builder')
    
    await helpers.navigateTo('Collections')
    await helpers.expectPageTitle('Collections')
    
    await helpers.navigateTo('Playbooks')
    await helpers.expectPageTitle('Playbook Builder')
    
    // Should still be logged in
    await expect(page.locator('button:has-text("Sign Out")')).toBeVisible()
  })

  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Try to access protected page directly
    await page.goto('/collections')
    
    // Should redirect to login
    await expect(page.locator('h2')).toContainText('Sign in to Sutra')
  })
})
