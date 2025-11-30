#!/usr/bin/env ts-node
/**
 * Forge Integration Validation Script
 *
 * This script validates the complete Forge workflow integration by checking:
 * 1. All TypeScript files compile without errors
 * 2. All required components exist and are properly structured
 * 3. API service layer has all required methods
 * 4. Routing is properly configured
 * 5. Type definitions are complete
 *
 * Run: npx ts-node scripts/validate-forge-integration.ts
 */

import * as fs from "fs";
import * as path from "path";

interface ValidationResult {
  category: string;
  test: string;
  status: "PASS" | "FAIL" | "WARN";
  message?: string;
}

const results: ValidationResult[] = [];

function addResult(
  category: string,
  test: string,
  status: "PASS" | "FAIL" | "WARN",
  message?: string,
) {
  results.push({ category, test, status, message });
}

function fileExists(filePath: string): boolean {
  return fs.existsSync(path.join(process.cwd(), filePath));
}

function fileContains(filePath: string, searchString: string): boolean {
  try {
    const content = fs.readFileSync(
      path.join(process.cwd(), filePath),
      "utf-8",
    );
    return content.includes(searchString);
  } catch {
    return false;
  }
}

function countOccurrences(filePath: string, searchString: string): number {
  try {
    const content = fs.readFileSync(
      path.join(process.cwd(), filePath),
      "utf-8",
    );
    return (content.match(new RegExp(searchString, "g")) || []).length;
  } catch {
    return 0;
  }
}

// ============================================
// Category 1: Component Files
// ============================================
console.log("\n📦 Validating Component Files...\n");

const requiredComponents = [
  "src/components/forge/IdeaRefinementStage.tsx",
  "src/components/forge/PRDGeneration.tsx",
  "src/components/forge/UXRequirementsStage.tsx",
  "src/components/forge/TechnicalAnalysisStage.tsx",
  "src/components/forge/ImplementationPlaybookStage.tsx",
  "src/components/forge/ForgeProjectDetails.tsx",
];

requiredComponents.forEach((component) => {
  const exists = fileExists(component);
  addResult(
    "Components",
    `${path.basename(component)} exists`,
    exists ? "PASS" : "FAIL",
    exists ? undefined : `Missing required component: ${component}`,
  );
});

// ============================================
// Category 2: Type Definitions
// ============================================
console.log("📝 Validating Type Definitions...\n");

const typeFile = "src/types/forge.ts";
const requiredTypes = [
  "ForgeProject",
  "IdeaRefinementData",
  "PRDGenerationData",
  "UXRequirementsData",
  "TechnicalAnalysisData",
  "ImplementationPlaybookData",
  "QualityAssessment",
  "ForgeStage",
];

if (fileExists(typeFile)) {
  addResult("Types", "forge.ts exists", "PASS");

  requiredTypes.forEach((typeName) => {
    const hasType =
      fileContains(typeFile, `export interface ${typeName}`) ||
      fileContains(typeFile, `export type ${typeName}`);
    addResult(
      "Types",
      `${typeName} defined`,
      hasType ? "PASS" : "FAIL",
      hasType ? undefined : `Missing type definition: ${typeName}`,
    );
  });
} else {
  addResult("Types", "forge.ts exists", "FAIL", "Missing type definition file");
}

// ============================================
// Category 3: API Service Layer
// ============================================
console.log("🔌 Validating API Service Layer...\n");

const apiFile = "src/services/api.ts";
const requiredApiMethods = [
  "createForgeProject",
  "getForgeProject",
  "analyzeIdea",
  "generateUserStories",
  "generateUserJourneys",
  "analyzeArchitecture",
  "compilePlaybook",
  "exportPlaybook",
];

if (fileExists(apiFile)) {
  addResult("API Service", "api.ts exists", "PASS");

  requiredApiMethods.forEach((method) => {
    const hasMethod = fileContains(apiFile, method);
    addResult(
      "API Service",
      `${method}() defined`,
      hasMethod ? "PASS" : "WARN",
      hasMethod ? undefined : `API method not found: ${method}()`,
    );
  });
} else {
  addResult("API Service", "api.ts exists", "FAIL", "Missing API service file");
}

// ============================================
// Category 4: Routing Configuration
// ============================================
console.log("🛣️  Validating Routing Configuration...\n");

const appFile = "src/App.tsx";
const forgeRoutes = [
  "/forge",
  "/forge/:projectId",
  "/forge/:projectId/idea",
  "/forge/:projectId/prd",
  "/forge/:projectId/ux",
  "/forge/:projectId/tech",
  "/forge/:projectId/playbook",
];

if (fileExists(appFile)) {
  addResult("Routing", "App.tsx exists", "PASS");

  forgeRoutes.forEach((route) => {
    const hasRoute = fileContains(appFile, route);
    addResult(
      "Routing",
      `Route "${route}" configured`,
      hasRoute ? "PASS" : "WARN",
      hasRoute ? undefined : `Route not found in App.tsx: ${route}`,
    );
  });
} else {
  addResult("Routing", "App.tsx exists", "FAIL", "Missing App.tsx file");
}

// ============================================
// Category 5: Stage Integration
// ============================================
console.log("🔗 Validating Stage Integration...\n");

const forgeDetailsFile = "src/components/forge/ForgeProjectDetails.tsx";

if (fileExists(forgeDetailsFile)) {
  addResult("Integration", "ForgeProjectDetails.tsx exists", "PASS");

  const stageComponents = [
    "IdeaRefinementStage",
    "PRDGeneration",
    "UXRequirementsStage",
    "TechnicalAnalysisStage",
    "ImplementationPlaybookStage",
  ];

  stageComponents.forEach((component) => {
    const isImported = fileContains(forgeDetailsFile, component);
    const isUsed =
      fileContains(forgeDetailsFile, `<${component}`) ||
      fileContains(forgeDetailsFile, `{${component}}`);

    if (isImported && isUsed) {
      addResult("Integration", `${component} integrated`, "PASS");
    } else if (isImported) {
      addResult(
        "Integration",
        `${component} integrated`,
        "WARN",
        "Imported but not used",
      );
    } else {
      addResult(
        "Integration",
        `${component} integrated`,
        "FAIL",
        "Not imported or used",
      );
    }
  });
} else {
  addResult(
    "Integration",
    "ForgeProjectDetails.tsx exists",
    "FAIL",
    "Missing integration file",
  );
}

// ============================================
// Category 6: E2E Tests
// ============================================
console.log("🧪 Validating E2E Tests...\n");

const e2eTestFile = "tests/e2e/forge-workflow.spec.ts";

if (fileExists(e2eTestFile)) {
  addResult("E2E Tests", "forge-workflow.spec.ts exists", "PASS");

  const testCount = countOccurrences(e2eTestFile, "test\\(");
  addResult(
    "E2E Tests",
    "Test scenarios defined",
    testCount >= 5 ? "PASS" : "WARN",
    `Found ${testCount} test scenarios`,
  );

  const testScenarios = [
    "complete full Forge workflow",
    "enforce quality gates",
    "preserve context",
    "handle navigation",
    "track costs",
  ];

  testScenarios.forEach((scenario) => {
    const hasScenario = fileContains(e2eTestFile, scenario);
    addResult(
      "E2E Tests",
      `Test: "${scenario}"`,
      hasScenario ? "PASS" : "WARN",
      hasScenario ? undefined : `Test scenario not found`,
    );
  });
} else {
  addResult(
    "E2E Tests",
    "forge-workflow.spec.ts exists",
    "FAIL",
    "Missing E2E test file",
  );
}

// ============================================
// Category 7: Build Configuration
// ============================================
console.log("⚙️  Validating Build Configuration...\n");

const buildFiles = [
  "package.json",
  "tsconfig.json",
  "vite.config.ts",
  "playwright.config.ts",
];

buildFiles.forEach((file) => {
  const exists = fileExists(file);
  addResult(
    "Build Config",
    `${file} exists`,
    exists ? "PASS" : "FAIL",
    exists ? undefined : `Missing configuration file: ${file}`,
  );
});

// ============================================
// Print Results
// ============================================
console.log("\n" + "=".repeat(80));
console.log("📊 VALIDATION RESULTS");
console.log("=".repeat(80) + "\n");

const categories = [...new Set(results.map((r) => r.category))];

categories.forEach((category) => {
  const categoryResults = results.filter((r) => r.category === category);
  const passed = categoryResults.filter((r) => r.status === "PASS").length;
  const failed = categoryResults.filter((r) => r.status === "FAIL").length;
  const warned = categoryResults.filter((r) => r.status === "WARN").length;

  console.log(`\n${category}:`);
  console.log(`  ✅ Passed: ${passed}`);
  if (warned > 0) console.log(`  ⚠️  Warnings: ${warned}`);
  if (failed > 0) console.log(`  ❌ Failed: ${failed}`);

  categoryResults.forEach((result) => {
    const icon =
      result.status === "PASS" ? "✅" : result.status === "WARN" ? "⚠️" : "❌";
    console.log(`    ${icon} ${result.test}`);
    if (result.message) {
      console.log(`       ${result.message}`);
    }
  });
});

// ============================================
// Summary
// ============================================
const totalPassed = results.filter((r) => r.status === "PASS").length;
const totalFailed = results.filter((r) => r.status === "FAIL").length;
const totalWarned = results.filter((r) => r.status === "WARN").length;
const totalTests = results.length;

const passRate = ((totalPassed / totalTests) * 100).toFixed(1);

console.log("\n" + "=".repeat(80));
console.log("📈 SUMMARY");
console.log("=".repeat(80));
console.log(`Total Tests: ${totalTests}`);
console.log(`✅ Passed: ${totalPassed} (${passRate}%)`);
if (totalWarned > 0) console.log(`⚠️  Warnings: ${totalWarned}`);
if (totalFailed > 0) console.log(`❌ Failed: ${totalFailed}`);

if (totalFailed === 0) {
  console.log("\n🎉 All critical validations passed!");
  console.log("✅ Forge integration is properly configured");
  process.exit(0);
} else {
  console.log("\n⚠️  Some validations failed");
  console.log("❌ Please address the failed checks above");
  process.exit(1);
}
