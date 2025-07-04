#!/usr/bin/env node

/**
 * Phase 2 Migration Script
 * Safely removes legacy configuration files after validation
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function migrateLegacyConfig() {
  console.log("🔄 Phase 2 Migration: Removing Legacy Configuration Files");
  console.log("========================================================\n");

  const configDir = path.join(path.dirname(__dirname), "src", "config");

  // Files to remove after migration
  const legacyFiles = ["authConfig.ts", "unifiedAuthConfig.ts", "runtime.ts"];

  // Check if consolidated config exists
  const consolidatedConfigExists = fs.existsSync(
    path.join(configDir, "index.ts"),
  );

  if (!consolidatedConfigExists) {
    console.log("❌ Cannot migrate: Consolidated config (index.ts) not found");
    return false;
  }

  console.log("✅ Consolidated config (index.ts) found");

  // Backup legacy files before removal
  const backupDir = path.join(configDir, "__legacy_backup");
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir);
    console.log(`📁 Created backup directory: ${backupDir}`);
  }

  // Move legacy files to backup
  let migratedCount = 0;
  for (const file of legacyFiles) {
    const filePath = path.join(configDir, file);
    const backupPath = path.join(backupDir, file);

    if (fs.existsSync(filePath)) {
      fs.renameSync(filePath, backupPath);
      console.log(`📦 Moved ${file} to backup`);
      migratedCount++;
    } else {
      console.log(`ℹ️  ${file} not found (already removed)`);
    }
  }

  // Update the test mocks to use consolidated config
  const mockDir = path.join(configDir, "__mocks__");
  if (fs.existsSync(mockDir)) {
    // Create consolidated mock file
    const mockIndexPath = path.join(mockDir, "index.ts");
    const mockContent = `/**
 * Mock configuration for testing
 * Consolidated mock to replace legacy individual config mocks
 */

export const AUTH_CONSTANTS = {
  TENANT_ID: "test-tenant-id",
  CLIENT_ID: "test-client-id",
  AUTHORITY: "https://login.microsoftonline.com/test-tenant-id",
  SCOPES: ["openid", "profile", "email", "offline_access"],
  DOMAIN: "test.onmicrosoft.com",
  ISSUER: "https://login.microsoftonline.com/test-tenant-id/v2.0",
};

export const getMSALConfig = () => ({
  auth: {
    clientId: AUTH_CONSTANTS.CLIENT_ID,
    authority: AUTH_CONSTANTS.AUTHORITY,
    redirectUri: "http://localhost:3000",
    postLogoutRedirectUri: "http://localhost:3000",
    navigateToLoginRequestUrl: true,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: () => {},
      piiLoggingEnabled: false,
    },
  },
});

export const getApiConfig = () => ({
  baseUrl: "http://localhost:7071/api",
  timeout: 30000,
  retryAttempts: 3,
});

export const getAppConfig = () => ({
  environment: "test",
  isProduction: false,
  isLocalDevelopment: true,
  isCustomDomain: false,
  hostname: "localhost",
  features: {
    enableGuestMode: true,
    enableMockAuth: true,
    enableAnalytics: false,
    enableDebugMode: true,
  },
  api: getApiConfig(),
  auth: {
    mode: "msal",
    ...AUTH_CONSTANTS,
  },
  app: {
    name: "Sutra Multi-LLM Prompt Studio",
    version: "1.0.0",
    description: "Weaving your AI solutions",
  },
});

export const getTokenRequestConfig = () => ({
  scopes: AUTH_CONSTANTS.SCOPES,
  forceRefresh: false,
});

export const getSilentTokenRequestConfig = () => ({
  scopes: AUTH_CONSTANTS.SCOPES,
  forceRefresh: false,
});

export const getLoginRequestConfig = () => ({
  scopes: AUTH_CONSTANTS.SCOPES,
  prompt: "select_account",
});

export const validateConfig = () => true;

// Legacy compatibility exports
export const msalConfig = getMSALConfig();
export const loginRequest = getLoginRequestConfig();
export const silentRequest = getSilentTokenRequestConfig();
export const getAuthMode = () => "msal";

export default {
  getMSALConfig,
  getAppConfig,
  getApiConfig,
  getTokenRequestConfig,
  getSilentTokenRequestConfig,
  getLoginRequestConfig,
  validateConfig,
  AUTH_CONSTANTS,
};
`;

    fs.writeFileSync(mockIndexPath, mockContent);
    console.log("📝 Created consolidated mock configuration");
  }

  console.log(`\n🎯 Migration Summary:`);
  console.log(`   - Legacy files moved to backup: ${migratedCount}`);
  console.log(`   - Consolidated config: ✅ Active`);
  console.log(`   - Mock configuration: ✅ Updated`);

  if (migratedCount > 0) {
    console.log("\n✅ Phase 2 Migration COMPLETE");
    console.log("📋 Next steps:");
    console.log("   1. Run validation to confirm all imports work");
    console.log("   2. Run tests to ensure no regressions");
    console.log("   3. Remove backup files after validation");
  } else {
    console.log("\n✅ Phase 2 Migration Already Complete");
  }

  return true;
}

// Run migration
const success = migrateLegacyConfig();
process.exit(success ? 0 : 1);
