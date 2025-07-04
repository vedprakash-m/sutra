#!/usr/bin/env node

/**
 * Phase 2 Validation Script
 * Validates configuration standardization and consolidation
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function searchFiles(dir, extensions = [".tsx", ".ts", ".js", ".jsx"]) {
  const files = [];

  function traverse(currentDir) {
    const items = fs.readdirSync(currentDir);

    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);

      if (
        stat.isDirectory() &&
        !item.startsWith(".") &&
        item !== "node_modules"
      ) {
        traverse(fullPath);
      } else if (
        stat.isFile() &&
        extensions.some((ext) => item.endsWith(ext))
      ) {
        files.push(fullPath);
      }
    }
  }

  traverse(dir);
  return files;
}

function validatePhase2() {
  console.log("🔍 Phase 2 Validation: Configuration Standardization");
  console.log("======================================================\n");

  const srcDir = path.join(path.dirname(__dirname), "src");
  const configDir = path.join(srcDir, "config");
  const files = searchFiles(srcDir);

  // Check config file structure
  const configFiles = fs.readdirSync(configDir);
  console.log("📁 Configuration Files:");
  configFiles.forEach((file) => {
    console.log(`   - ${file}`);
  });

  // Check for consolidated config usage
  let consolidatedImports = 0;
  let legacyImports = 0;
  let unifiedConfigImports = 0;
  let authConfigImports = 0;
  let runtimeConfigImports = 0;

  const issues = [];

  for (const file of files) {
    const content = fs.readFileSync(file, "utf8");
    const relativePath = path.relative(process.cwd(), file);

    // Check for consolidated config imports
    if (
      content.includes('from "@/config"') ||
      content.includes('from "../config"')
    ) {
      consolidatedImports++;
    }

    // Check for legacy config imports
    if (
      content.includes('from "@/config/authConfig"') ||
      content.includes('from "./authConfig"')
    ) {
      authConfigImports++;
      issues.push(`🟡 ${relativePath} - Using legacy authConfig import`);
    }

    if (
      content.includes('from "@/config/unifiedAuthConfig"') ||
      content.includes('from "./unifiedAuthConfig"')
    ) {
      unifiedConfigImports++;
      issues.push(`🟡 ${relativePath} - Using legacy unifiedAuthConfig import`);
    }

    if (
      content.includes('from "@/config/runtime"') ||
      content.includes('from "./runtime"')
    ) {
      runtimeConfigImports++;
      issues.push(`🟡 ${relativePath} - Using legacy runtime import`);
    }
  }

  console.log("\n📊 Configuration Import Analysis:");
  console.log(`   - Consolidated config imports: ${consolidatedImports}`);
  console.log(`   - Legacy authConfig imports: ${authConfigImports}`);
  console.log(`   - Legacy unifiedAuthConfig imports: ${unifiedConfigImports}`);
  console.log(`   - Legacy runtime imports: ${runtimeConfigImports}`);
  console.log(`   - Total files scanned: ${files.length}`);

  // Check if index.ts exists
  const indexExists = fs.existsSync(path.join(configDir, "index.ts"));
  console.log(`\n🏗️  Configuration Architecture:`);
  console.log(
    `   - Consolidated config (index.ts): ${indexExists ? "✅" : "❌"}`,
  );
  console.log(
    `   - Legacy authConfig.ts: ${fs.existsSync(path.join(configDir, "authConfig.ts")) ? "🟡 (needs removal)" : "✅"}`,
  );
  console.log(
    `   - Legacy unifiedAuthConfig.ts: ${fs.existsSync(path.join(configDir, "unifiedAuthConfig.ts")) ? "🟡 (needs removal)" : "✅"}`,
  );
  console.log(
    `   - Legacy runtime.ts: ${fs.existsSync(path.join(configDir, "runtime.ts")) ? "🟡 (needs removal)" : "✅"}`,
  );

  if (issues.length > 0) {
    console.log("\n🚨 Issues Found:");
    issues.forEach((issue) => console.log(`   ${issue}`));
  }

  console.log("\n🎯 Phase 2 Status:");
  const legacyTotal =
    authConfigImports + unifiedConfigImports + runtimeConfigImports;
  if (legacyTotal === 0 && consolidatedImports > 0 && indexExists) {
    console.log(
      "✅ Phase 2 COMPLETE: All configuration successfully consolidated",
    );
  } else if (consolidatedImports > 0 && indexExists) {
    console.log(
      "🟡 Phase 2 IN PROGRESS: Some legacy imports still need migration",
    );
  } else {
    console.log("❌ Phase 2 FAILED: Configuration consolidation not started");
  }

  return {
    complete: legacyTotal === 0 && consolidatedImports > 0 && indexExists,
    consolidatedImports,
    legacyImports: legacyTotal,
    issues,
  };
}

// Run validation
const result = validatePhase2();
process.exit(result.complete ? 0 : 1);
