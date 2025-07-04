/**
 * Unified Authentication Configuration
 * Single source of truth for all authentication settings per Apps_Auth_Requirement.md
 *
 * This configuration ensures consistent Entra ID authentication across all environments
 * and eliminates the dual authentication paradigm that was causing integration issues.
 */

import { Configuration } from "@azure/msal-browser";

// Vedprakash Domain Authentication Constants (Apps_Auth_Requirement.md)
export const VEDPRAKASH_CONSTANTS = {
  TENANT_ID: "80fe68b7-105c-4fb9-ab03-c9a818e35848", // vedid.onmicrosoft.com
  CLIENT_ID: "db1e3417-e353-4255-b05e-2e1fffe25692", // Sutra app registration
  AUTHORITY:
    "https://login.microsoftonline.com/80fe68b7-105c-4fb9-ab03-c9a818e35848",
  SCOPES: ["openid", "profile", "email", "offline_access"],
  DOMAIN: "vedid.onmicrosoft.com",
  ISSUER:
    "https://login.microsoftonline.com/80fe68b7-105c-4fb9-ab03-c9a818e35848/v2.0",
} as const;

// Environment Detection
const isProduction =
  window.location.hostname.includes("azurestaticapps.net") ||
  window.location.hostname === "sutra.vedprakash.net";
const isLocalDevelopment = window.location.hostname === "localhost";

// API Base URL Configuration
export const getApiBaseUrl = (): string => {
  if (isProduction) {
    return "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api";
  }

  // For local development, check if local API is available
  // This will be determined by the presence of local API server
  return "/api"; // Vite proxy will handle routing to local API
};

// Unified Authentication Configuration
export const getUnifiedAuthConfig = (): Configuration => {
  const baseConfig: Configuration = {
    auth: {
      clientId: VEDPRAKASH_CONSTANTS.CLIENT_ID,
      authority: VEDPRAKASH_CONSTANTS.AUTHORITY,
      redirectUri: window.location.origin,
      postLogoutRedirectUri: window.location.origin,
      navigateToLoginRequestUrl: true,
    },
    cache: {
      cacheLocation: "sessionStorage", // Use sessionStorage for SSO across tabs
      storeAuthStateInCookie: false,
    },
    system: {
      loggerOptions: {
        loggerCallback: (level, message, containsPii) => {
          if (containsPii) return;

          switch (level) {
            case 0: // Error
              console.error(`[MSAL] ${message}`);
              break;
            case 1: // Warning
              console.warn(`[MSAL] ${message}`);
              break;
            case 2: // Info
              console.info(`[MSAL] ${message}`);
              break;
            case 3: // Verbose
              if (process.env.NODE_ENV === "development") {
                console.debug(`[MSAL] ${message}`);
              }
              break;
          }
        },
        logLevel: process.env.NODE_ENV === "development" ? 3 : 1,
      },
    },
  };

  return baseConfig;
};

// Token Request Configuration
export const getTokenRequestConfig = () => ({
  scopes: ["openid", "profile", "email", "offline_access"] as string[],
  forceRefresh: false,
});

// Silent Token Request Configuration
export const getSilentTokenRequestConfig = () => ({
  scopes: ["openid", "profile", "email", "offline_access"] as string[],
  forceRefresh: false,
});

// Login Request Configuration
export const getLoginRequestConfig = () => ({
  scopes: ["openid", "profile", "email", "offline_access"] as string[],
  prompt: "select_account",
});

// Application Configuration
export const getAppConfig = () => ({
  // API Configuration
  apiBaseUrl: getApiBaseUrl(),

  // Authentication Configuration
  clientId: VEDPRAKASH_CONSTANTS.CLIENT_ID,
  tenantId: VEDPRAKASH_CONSTANTS.TENANT_ID,
  authority: VEDPRAKASH_CONSTANTS.AUTHORITY,

  // Environment Configuration
  isProduction,
  isLocalDevelopment,

  // Feature Flags
  enableGuestMode: true,
  enableMockAuth: false, // Always false - only use real Entra ID

  // Vedprakash Domain Configuration
  vedprakashDomain: true,
  customDomain: window.location.hostname === "sutra.vedprakash.net",

  // Debugging
  enableDebugLogs: process.env.NODE_ENV === "development",
});

// Validation Functions
export const validateAuthConfiguration = (): boolean => {
  const config = getAppConfig();

  // Validate required configuration
  if (!config.clientId || config.clientId.includes("00000000-0000-0000")) {
    console.error("Invalid client ID configuration");
    return false;
  }

  if (!config.tenantId) {
    console.error("Invalid tenant ID configuration");
    return false;
  }

  if (!config.authority) {
    console.error("Invalid authority configuration");
    return false;
  }

  if (!config.apiBaseUrl) {
    console.error("Invalid API base URL configuration");
    return false;
  }

  return true;
};

// Export unified configuration
export default {
  getUnifiedAuthConfig,
  getTokenRequestConfig,
  getSilentTokenRequestConfig,
  getLoginRequestConfig,
  getAppConfig,
  validateAuthConfiguration,
  VEDPRAKASH_CONSTANTS,
};
