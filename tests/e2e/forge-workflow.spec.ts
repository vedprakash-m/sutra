/**
 * E2E Tests for Forge Workflow (5 Stages)
 * Tests the complete end-to-end flow from idea refinement through implementation playbook
 */
import { test, expect } from "@playwright/test";
import { TestHelpers } from "./helpers";

test.describe("Forge Workflow - Complete 5-Stage Journey", () => {
  let helpers: TestHelpers;
  let projectId: string;
  let projectName: string;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
    await helpers.loginAsUser("user");
    projectName = `E2E Test Project ${Date.now()}`;
  });

  test.afterEach(async ({ page }) => {
    // Clean up test project if needed
    if (projectId) {
      try {
        await page.request.delete(
          `http://localhost:7071/api/forge/projects/${projectId}`,
          {
            headers: {
              "Content-Type": "application/json",
              "x-test-auth": "user",
            },
          },
        );
        console.log(`🧹 Cleaned up test project: ${projectId}`);
      } catch (error) {
        console.log("⚠️ Could not clean up test project:", error);
      }
    }
  });

  test("should complete full Forge workflow from Stage 1 to Stage 5", async ({
    page,
  }) => {
    // Navigate to Forge
    await helpers.navigateTo("Forge");
    await expect(page.locator("h1")).toContainText("Forge Projects");

    // ==========================================
    // CREATE NEW PROJECT
    // ==========================================
    console.log("\n📝 Creating new Forge project...");

    // Click "New Project" button
    await page.click('button:has-text("New Project")');

    // Fill project details
    await page.fill('input[placeholder*="project name"]', projectName);
    await page.fill(
      'textarea[placeholder*="initial idea"]',
      "Build a task management app with AI-powered prioritization and team collaboration features",
    );

    // Select LLM (GPT-4)
    await page.click('select[name="selectedLLM"]');
    await page.selectOption('select[name="selectedLLM"]', "gpt-4");

    // Create project
    await page.click('button:has-text("Create Project")');

    // Wait for project to be created and navigate to details
    await page.waitForURL(/\/forge\/[^/]+/, { timeout: 10000 });

    // Extract project ID from URL
    const url = page.url();
    const match = url.match(/\/forge\/([^/]+)/);
    projectId = match ? match[1] : "";

    console.log(`✅ Project created with ID: ${projectId}`);

    // Verify we're on the project details page
    await expect(page.locator("h1")).toContainText(projectName);

    // ==========================================
    // STAGE 1: IDEA REFINEMENT
    // ==========================================
    console.log("\n🔍 Stage 1: Idea Refinement");

    // Verify current stage indicator
    await expect(page.locator('[data-stage="idea_refinement"]')).toHaveClass(
      /active|current/,
    );

    // Generate initial analysis
    await page.click('button:has-text("Analyze Idea")');

    // Wait for analysis to complete (may take a few seconds)
    await page.waitForSelector('[data-analysis-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ Initial analysis generated");

    // Answer refinement questions
    await page.click('button:has-text("Answer Questions")');

    // Fill in question responses
    const questionInputs = page.locator("textarea[data-question-input]");
    const questionCount = await questionInputs.count();

    for (let i = 0; i < Math.min(questionCount, 3); i++) {
      await questionInputs
        .nth(i)
        .fill(
          `This is a detailed answer to question ${i + 1} about the project scope, target users, and technical requirements.`,
        );
    }

    await page.click('button:has-text("Submit Answers")');

    // Generate stakeholder interviews
    await page.click('button:has-text("Generate Interview Questions")');
    await page.waitForSelector('[data-interviews-complete="true"]', {
      timeout: 20000,
    });

    console.log("✅ Stakeholder interviews generated");

    // Check quality score
    const qualityScore = await page
      .locator("[data-quality-score]")
      .textContent();
    console.log(`Quality Score: ${qualityScore}`);

    // Complete Stage 1 (quality must be >= 75%)
    await page.click('button:has-text("Complete Stage")');

    // Wait for confirmation or quality gate check
    await page.waitForTimeout(2000);

    // If quality is insufficient, improve it
    const qualityGateVisible = await page
      .locator("text=/Quality threshold not met/i")
      .isVisible()
      .catch(() => false);

    if (qualityGateVisible) {
      console.log("⚠️ Quality threshold not met, generating improvements...");
      await page.click('button:has-text("Generate Improvements")');
      await page.waitForTimeout(5000);
      await page.click('button:has-text("Complete Stage")');
    }

    // Verify transition to Stage 2
    await expect(page.locator('[data-stage="prd_generation"]')).toHaveClass(
      /active|current/,
      { timeout: 10000 },
    );

    console.log("✅ Stage 1 completed, transitioned to Stage 2");

    // ==========================================
    // STAGE 2: PRD GENERATION
    // ==========================================
    console.log("\n📋 Stage 2: PRD Generation");

    // Verify Stage 2 is active
    await expect(page.locator("h2")).toContainText("PRD Generation");

    // Generate user stories
    await page.click('button:has-text("Generate User Stories")');
    await page.waitForSelector('[data-user-stories-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ User stories generated");

    // Generate requirements
    await page.click('button:has-text("Generate Requirements")');
    await page.waitForSelector('[data-requirements-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ Requirements generated");

    // Generate acceptance criteria
    await page.click('button:has-text("Generate Acceptance Criteria")');
    await page.waitForSelector('[data-acceptance-criteria-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ Acceptance criteria generated");

    // Generate PRD document
    await page.click('button:has-text("Compile PRD Document")');
    await page.waitForSelector('[data-prd-document-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ PRD document compiled");

    // Check quality score (must be >= 80%)
    const prdQualityScore = await page
      .locator("[data-quality-score]")
      .textContent();
    console.log(`PRD Quality Score: ${prdQualityScore}`);

    // Complete Stage 2
    await page.click('button:has-text("Complete Stage")');

    // Handle quality gate if needed
    const prdQualityGateVisible = await page
      .locator("text=/Quality threshold not met/i")
      .isVisible()
      .catch(() => false);

    if (prdQualityGateVisible) {
      console.log("⚠️ PRD quality threshold not met, refining...");
      await page.click('button:has-text("Refine PRD")');
      await page.waitForTimeout(5000);
      await page.click('button:has-text("Complete Stage")');
    }

    // Verify transition to Stage 3
    await expect(page.locator('[data-stage="ux_requirements"]')).toHaveClass(
      /active|current/,
      { timeout: 10000 },
    );

    console.log("✅ Stage 2 completed, transitioned to Stage 3");

    // ==========================================
    // STAGE 3: UX REQUIREMENTS
    // ==========================================
    console.log("\n🎨 Stage 3: UX Requirements");

    // Verify Stage 3 is active
    await expect(page.locator("h2")).toContainText("UX Requirements");

    // Generate user journeys
    await page.click('button:has-text("Generate User Journeys")');
    await page.waitForSelector('[data-user-journeys-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ User journeys generated");

    // Generate wireframes
    await page.click('button:has-text("Generate Wireframes")');
    await page.waitForSelector('[data-wireframes-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ Wireframes generated");

    // Generate component specifications
    await page.click('button:has-text("Generate Component Specs")');
    await page.waitForSelector('[data-component-specs-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ Component specifications generated");

    // Validate accessibility (WCAG 2.1 AA)
    await page.click('button:has-text("Validate Accessibility")');
    await page.waitForSelector('[data-accessibility-validated="true"]', {
      timeout: 20000,
    });

    console.log("✅ Accessibility validated");

    // Check quality score (must be >= 85% + accessibility >= 90%)
    const uxQualityScore = await page
      .locator("[data-quality-score]")
      .textContent();
    const accessibilityScore = await page
      .locator("[data-accessibility-score]")
      .textContent();
    console.log(
      `UX Quality Score: ${uxQualityScore}, Accessibility: ${accessibilityScore}`,
    );

    // Complete Stage 3
    await page.click('button:has-text("Complete Stage")');

    // Handle quality gate if needed
    const uxQualityGateVisible = await page
      .locator("text=/Quality threshold not met/i")
      .isVisible()
      .catch(() => false);

    if (uxQualityGateVisible) {
      console.log("⚠️ UX quality threshold not met, improving...");
      await page.click('button:has-text("Improve UX Design")');
      await page.waitForTimeout(5000);
      await page.click('button:has-text("Complete Stage")');
    }

    // Verify transition to Stage 4
    await expect(page.locator('[data-stage="technical_analysis"]')).toHaveClass(
      /active|current/,
      { timeout: 10000 },
    );

    console.log("✅ Stage 3 completed, transitioned to Stage 4");

    // ==========================================
    // STAGE 4: TECHNICAL ANALYSIS
    // ==========================================
    console.log("\n⚙️ Stage 4: Technical Analysis");

    // Verify Stage 4 is active
    await expect(page.locator("h2")).toContainText("Technical Analysis");

    // Select multiple LLMs for consensus
    await page.check('input[value="gpt-4"]');
    await page.check('input[value="claude-3-5-sonnet-20241022"]');
    await page.check('input[value="gemini-1.5-pro"]');

    console.log("✅ Selected 3 LLMs for consensus analysis");

    // Analyze architecture
    await page.click('button:has-text("Analyze Architecture")');
    await page.waitForSelector('[data-architecture-analysis-complete="true"]', {
      timeout: 60000, // Multi-LLM may take longer
    });

    console.log("✅ Architecture analysis complete (multi-LLM consensus)");

    // Verify consensus data is displayed
    await expect(page.locator("[data-consensus-score]")).toBeVisible();

    const consensusScore = await page
      .locator("[data-consensus-score]")
      .textContent();
    console.log(`Consensus Score: ${consensusScore}`);

    // Generate technical specifications
    await page.click('button:has-text("Generate Technical Specs")');
    await page.waitForSelector('[data-technical-specs-complete="true"]', {
      timeout: 30000,
    });

    console.log("✅ Technical specifications generated");

    // Complete Stage 4
    await page.click('button:has-text("Complete Stage")');

    // Verify transition to Stage 5
    await expect(
      page.locator('[data-stage="implementation_playbook"]'),
    ).toHaveClass(/active|current/, { timeout: 10000 });

    console.log("✅ Stage 4 completed, transitioned to Stage 5");

    // ==========================================
    // STAGE 5: IMPLEMENTATION PLAYBOOK
    // ==========================================
    console.log("\n🚀 Stage 5: Implementation Playbook");

    // Verify Stage 5 is active
    await expect(page.locator("h2")).toContainText("Implementation Playbook");

    // Compile playbook from all previous stages
    await page.click('button:has-text("Compile Playbook")');
    await page.waitForSelector('[data-playbook-compiled="true"]', {
      timeout: 30000,
    });

    console.log("✅ Implementation playbook compiled");

    // Verify all sections are present
    await expect(page.locator("text=Project Overview")).toBeVisible();
    await expect(page.locator("text=Architecture")).toBeVisible();
    await expect(page.locator("text=Development Workflow")).toBeVisible();
    await expect(page.locator("text=Coding Prompts")).toBeVisible();

    // Test export functionality
    console.log("\n📥 Testing export functionality...");

    // Export as Markdown
    const [markdownDownload] = await Promise.all([
      page.waitForEvent("download", { timeout: 10000 }),
      page.click('button:has-text("Export Markdown")'),
    ]);
    expect(markdownDownload.suggestedFilename()).toContain(".md");
    console.log("✅ Markdown export successful");

    // Export as JSON
    const [jsonDownload] = await Promise.all([
      page.waitForEvent("download", { timeout: 10000 }),
      page.click('button:has-text("Export JSON")'),
    ]);
    expect(jsonDownload.suggestedFilename()).toContain(".json");
    console.log("✅ JSON export successful");

    // Export as PDF
    const [pdfDownload] = await Promise.all([
      page.waitForEvent("download", { timeout: 15000 }),
      page.click('button:has-text("Export PDF")'),
    ]);
    expect(pdfDownload.suggestedFilename()).toContain(".pdf");
    console.log("✅ PDF export successful");

    // Export as ZIP (complete package)
    const [zipDownload] = await Promise.all([
      page.waitForEvent("download", { timeout: 15000 }),
      page.click('button:has-text("Export Complete Package")'),
    ]);
    expect(zipDownload.suggestedFilename()).toContain(".zip");
    console.log("✅ ZIP export successful");

    // Complete Stage 5
    await page.click('button:has-text("Mark Complete")');

    // Verify project marked as complete
    await expect(page.locator('[data-project-status="completed"]')).toBeVisible(
      {
        timeout: 5000,
      },
    );

    console.log("✅ Stage 5 completed - Full Forge workflow finished!");

    // ==========================================
    // VERIFY FINAL PROJECT STATE
    // ==========================================
    console.log("\n✅ Verifying final project state...");

    // All stages should show as completed
    await expect(
      page.locator('[data-stage="idea_refinement"][data-status="completed"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-stage="prd_generation"][data-status="completed"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-stage="ux_requirements"][data-status="completed"]'),
    ).toBeVisible();
    await expect(
      page.locator(
        '[data-stage="technical_analysis"][data-status="completed"]',
      ),
    ).toBeVisible();
    await expect(
      page.locator(
        '[data-stage="implementation_playbook"][data-status="completed"]',
      ),
    ).toBeVisible();

    console.log("✅ All stages verified as completed");

    // Navigate back to Forge projects list
    await page.click('a[href="/forge"]');

    // Verify project appears in list with "Completed" status
    await expect(
      page
        .locator(`text=${projectName}`)
        .locator("..")
        .locator("text=/Completed/i"),
    ).toBeVisible();

    console.log("\n🎉 FULL FORGE WORKFLOW TEST COMPLETED SUCCESSFULLY!");
  });

  test("should enforce quality gates between stages", async ({ page }) => {
    console.log("\n🔒 Testing quality gate enforcement...");

    // Create project with minimal data
    await helpers.navigateTo("Forge");
    await page.click('button:has-text("New Project")');

    await page.fill(
      'input[placeholder*="project name"]',
      `Quality Gate Test ${Date.now()}`,
    );
    await page.fill(
      'textarea[placeholder*="initial idea"]',
      "Minimal idea", // Intentionally minimal to test quality gates
    );

    await page.click('button:has-text("Create Project")');
    await page.waitForURL(/\/forge\/[^/]+/);

    const url = page.url();
    const match = url.match(/\/forge\/([^/]+)/);
    projectId = match ? match[1] : "";

    // Try to complete Stage 1 without meeting quality threshold
    await page.click('button:has-text("Analyze Idea")');
    await page.waitForTimeout(5000);

    await page.click('button:has-text("Complete Stage")');

    // Should show quality gate warning
    await expect(page.locator("text=/Quality threshold not met/i")).toBeVisible(
      { timeout: 5000 },
    );

    console.log("✅ Quality gate correctly prevents progression");

    // Verify user cannot manually navigate to next stage
    const stage2Button = page.locator('[data-stage="prd_generation"]');
    if (await stage2Button.isVisible()) {
      await expect(stage2Button).toBeDisabled();
    }

    console.log("✅ Stage navigation correctly locked");
  });

  test("should preserve context across stage transitions", async ({ page }) => {
    console.log("\n🔄 Testing context preservation...");

    await helpers.navigateTo("Forge");
    await page.click('button:has-text("New Project")');

    const testIdea =
      "Context Preservation Test - AI-powered analytics dashboard";

    await page.fill(
      'input[placeholder*="project name"]',
      `Context Test ${Date.now()}`,
    );
    await page.fill('textarea[placeholder*="initial idea"]', testIdea);

    await page.click('button:has-text("Create Project")');
    await page.waitForURL(/\/forge\/[^/]+/);

    const url = page.url();
    const match = url.match(/\/forge\/([^/]+)/);
    projectId = match ? match[1] : "";

    // Complete Stage 1 with specific data
    await page.click('button:has-text("Analyze Idea")');
    await page.waitForSelector('[data-analysis-complete="true"]', {
      timeout: 30000,
    });

    // Capture Stage 1 key insights
    const stage1Insights = await page
      .locator("[data-key-insights]")
      .textContent();
    console.log(
      `Stage 1 Insights captured: ${stage1Insights?.substring(0, 50)}...`,
    );

    // Progress to Stage 2 (assuming quality is met)
    await page.click('button:has-text("Answer Questions")');
    const questionInputs = page.locator("textarea[data-question-input]");
    const count = await questionInputs.count();

    for (let i = 0; i < Math.min(count, 3); i++) {
      await questionInputs.nth(i).fill("Detailed context answer");
    }

    await page.click('button:has-text("Submit Answers")');
    await page.click('button:has-text("Complete Stage")');

    // Wait for Stage 2
    await expect(page.locator('[data-stage="prd_generation"]')).toHaveClass(
      /active|current/,
      { timeout: 10000 },
    );

    // Verify Stage 2 has access to Stage 1 context
    await expect(page.locator("text=From Idea Refinement")).toBeVisible();

    // Check if original idea is referenced
    const contextSection = page.locator("[data-context-from-stage-1]");
    if (await contextSection.isVisible()) {
      const contextText = await contextSection.textContent();
      expect(contextText).toContain("analytics"); // From our test idea
      console.log("✅ Stage 1 context preserved in Stage 2");
    }
  });

  test("should handle navigation between stages correctly", async ({
    page,
  }) => {
    console.log("\n🧭 Testing stage navigation...");

    // Create and setup a project
    await helpers.navigateTo("Forge");
    await page.click('button:has-text("New Project")');

    await page.fill(
      'input[placeholder*="project name"]',
      `Navigation Test ${Date.now()}`,
    );
    await page.fill(
      'textarea[placeholder*="initial idea"]',
      "Navigation test project idea",
    );

    await page.click('button:has-text("Create Project")');
    await page.waitForURL(/\/forge\/[^/]+/);

    const url = page.url();
    const match = url.match(/\/forge\/([^/]+)/);
    projectId = match ? match[1] : "";

    // Verify Stage 1 is active
    await expect(page.locator('[data-stage="idea_refinement"]')).toHaveClass(
      /active|current/,
    );

    // Verify future stages are disabled/locked
    const stage2Nav = page.locator('[data-stage-nav="prd_generation"]');
    const stage3Nav = page.locator('[data-stage-nav="ux_requirements"]');

    if (await stage2Nav.isVisible()) {
      await expect(stage2Nav).toBeDisabled();
      console.log("✅ Stage 2 navigation correctly disabled");
    }

    if (await stage3Nav.isVisible()) {
      await expect(stage3Nav).toBeDisabled();
      console.log("✅ Stage 3 navigation correctly disabled");
    }

    // Complete Stage 1
    await page.click('button:has-text("Analyze Idea")');
    await page.waitForTimeout(10000);
    await page.click('button:has-text("Complete Stage")');

    // Stage 2 should now be accessible
    await expect(page.locator('[data-stage="prd_generation"]')).toHaveClass(
      /active|current/,
      { timeout: 10000 },
    );

    console.log(
      "✅ Successfully navigated to Stage 2 after completing Stage 1",
    );
  });
});

test.describe("Forge Workflow - Cost Tracking", () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
    await helpers.loginAsUser("user");
  });

  test("should track costs across all Forge stages", async ({ page }) => {
    console.log("\n💰 Testing cost tracking in Forge workflow...");

    await helpers.navigateTo("Forge");
    await page.click('button:has-text("New Project")');

    await page.fill(
      'input[placeholder*="project name"]',
      `Cost Tracking Test ${Date.now()}`,
    );
    await page.fill(
      'textarea[placeholder*="initial idea"]',
      "Test project for cost tracking validation",
    );

    await page.click('button:has-text("Create Project")');
    await page.waitForURL(/\/forge\/[^/]+/);

    // Capture initial cost
    const initialCost = await page.locator("[data-total-cost]").textContent();
    console.log(`Initial cost: ${initialCost}`);

    // Perform an API call (idea analysis)
    await page.click('button:has-text("Analyze Idea")');
    await page.waitForTimeout(10000);

    // Verify cost increased
    const updatedCost = await page.locator("[data-total-cost]").textContent();
    console.log(`Updated cost: ${updatedCost}`);

    expect(updatedCost).not.toBe(initialCost);
    console.log("✅ Cost tracking working correctly");

    // Verify cost breakdown is visible
    await page.click("[data-show-cost-details]");
    await expect(page.locator("text=Cost Breakdown")).toBeVisible();

    // Verify stage-specific costs
    await expect(
      page.locator('[data-stage-cost="idea_refinement"]'),
    ).toBeVisible();
  });
});

test.describe("Forge Workflow - Error Handling", () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
    await helpers.loginAsUser("user");
  });

  test("should handle API errors gracefully", async ({ page }) => {
    console.log("\n⚠️ Testing error handling...");

    // Intercept API calls and simulate errors
    await page.route("**/api/forge/**", (route) => {
      route.abort("failed");
    });

    await helpers.navigateTo("Forge");
    await page.click('button:has-text("New Project")');

    await page.fill(
      'input[placeholder*="project name"]',
      `Error Test ${Date.now()}`,
    );
    await page.fill(
      'textarea[placeholder*="initial idea"]',
      "Error handling test",
    );

    await page.click('button:has-text("Create Project")');

    // Should show error message
    await expect(page.locator("text=/Error|Failed|Try again/i")).toBeVisible({
      timeout: 10000,
    });

    console.log("✅ Error message displayed correctly");

    // Verify user can retry
    const retryButton = page.locator("button:has-text(/Retry|Try Again/i)");
    if (await retryButton.isVisible()) {
      await expect(retryButton).toBeEnabled();
      console.log("✅ Retry functionality available");
    }
  });
});
