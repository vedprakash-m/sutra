#!/usr/bin/env node

/**
 * Phase 3 Validation Script
 * Validates backend integration cleanup and API standardization
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function searchFiles(dir, extensions = [".py"]) {
  const files = [];

  function traverse(currentDir) {
    try {
      const items = fs.readdirSync(currentDir);

      for (const item of items) {
        const fullPath = path.join(currentDir, item);
        const stat = fs.statSync(fullPath);

        if (
          stat.isDirectory() &&
          !item.startsWith(".") &&
          !item.includes("__pycache__")
        ) {
          traverse(fullPath);
        } else if (
          stat.isFile() &&
          extensions.some((ext) => item.endsWith(ext))
        ) {
          files.push(fullPath);
        }
      }
    } catch (err) {
      // Skip directories we can't read
    }
  }

  traverse(dir);
  return files;
}

function validatePhase3() {
  console.log("🔍 Phase 3 Validation: Backend Integration Cleanup");
  console.log("===================================================\n");

  const apiDir = path.join(path.dirname(__dirname), "api");
  const files = searchFiles(apiDir);

  console.log(`📁 Found ${files.length} Python files in API directory\n`);

  // Authentication patterns analysis
  let unifiedAuthImports = 0;
  let legacyAuthImports = 0;
  let inconsistentPatterns = [];
  let authModules = [];

  // Response format analysis
  let inconsistentResponses = [];
  let fieldNamingIssues = [];

  // Error handling analysis
  let errorHandlingPatterns = [];

  for (const file of files) {
    try {
      const content = fs.readFileSync(file, "utf8");
      const relativePath = path.relative(process.cwd(), file);

      // Check authentication imports
      if (
        content.includes("shared.unified_auth") ||
        content.includes("from shared.unified_auth")
      ) {
        unifiedAuthImports++;
      }

      if (
        content.includes("shared.auth") &&
        !content.includes("shared.unified_auth") &&
        !relativePath.includes("test") &&
        !relativePath.includes("mocking")
      ) {
        legacyAuthImports++;
        inconsistentPatterns.push(
          `🟡 ${relativePath} - Using legacy shared.auth`,
        );
      }

      // Track auth module files
      if (
        relativePath.includes("shared") &&
        (relativePath.includes("auth") || relativePath.includes("Auth"))
      ) {
        authModules.push(relativePath);
      }

      // Check for inconsistent response patterns - but exclude converter utilities
      if (
        content.includes("snake_case") &&
        content.includes("camelCase") &&
        !relativePath.includes("fieldConverter") &&
        !relativePath.includes("converter")
      ) {
        fieldNamingIssues.push(
          `🟡 ${relativePath} - Mixed snake_case/camelCase patterns`,
        );
      }

      // Check error handling patterns
      if (content.includes("return {") && content.includes("error")) {
        errorHandlingPatterns.push(relativePath);
      }
    } catch (err) {
      // Skip files we can't read
    }
  }

  console.log("📊 Authentication Integration Analysis:");
  console.log(`   - Files using unified_auth: ${unifiedAuthImports}`);
  console.log(`   - Files using legacy auth: ${legacyAuthImports}`);
  console.log(`   - Total Python files: ${files.length}`);

  console.log("\\n🏗️  Auth Module Files:");
  authModules.forEach((module) => {
    const isUnified = module.includes("unified_auth");
    const isLegacy = module.includes("auth.py") && !module.includes("unified");
    const isMocking = module.includes("mocking") || module.includes("test");

    let status = "✅";
    if (isLegacy && !isMocking) status = "🟡";
    if (isMocking) status = "🔧";

    console.log(`   ${status} ${module}`);
  });

  if (inconsistentPatterns.length > 0) {
    console.log("\\n🚨 Authentication Issues:");
    inconsistentPatterns.forEach((issue) => console.log(`   ${issue}`));
  }

  if (fieldNamingIssues.length > 0) {
    console.log("\\n🚨 Field Naming Issues:");
    fieldNamingIssues.forEach((issue) => console.log(`   ${issue}`));
  }

  console.log("\\n🎯 Phase 3 Status:");
  const hasLegacyIssues = legacyAuthImports > 0 || fieldNamingIssues.length > 0;
  const isWellAdopted = unifiedAuthImports > legacyAuthImports;

  if (!hasLegacyIssues && isWellAdopted) {
    console.log(
      "✅ Phase 3 COMPLETE: Backend integration is clean and standardized",
    );
  } else if (isWellAdopted) {
    console.log(
      "🟡 Phase 3 IN PROGRESS: Mostly unified but some cleanup needed",
    );
  } else {
    console.log(
      "🔴 Phase 3 NEEDS WORK: Significant backend integration issues remain",
    );
  }

  // Check for OpenAPI specification
  const openapiPath = path.join(apiDir, "openapi.yaml");
  const hasOpenAPI = fs.existsSync(openapiPath);
  console.log(`\\n📋 API Documentation:`);
  console.log(`   - OpenAPI specification: ${hasOpenAPI ? "✅" : "❌"}`);

  return {
    complete: !hasLegacyIssues && isWellAdopted && hasOpenAPI,
    unifiedAuthImports,
    legacyAuthImports,
    issues: inconsistentPatterns.concat(fieldNamingIssues),
  };
}

// Run validation
const result = validatePhase3();
process.exit(result.complete ? 0 : 1);
