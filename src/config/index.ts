/**
 * Consolidated Application Configuration
 * Single source of truth for all application settings
 *
 * This replaces:
 * - authConfig.ts (authentication settings)
 * - unifiedAuthConfig.ts (MSAL configuration)
 * - runtime.ts (environment detection)
 *
 * Addresses Phase 2 of architectural remediation plan
 */

import { Configuration } from "@azure/msal-browser";

// Environment Detection
const getEnvironmentInfo = () => {
  const hostname = window.location.hostname;
  const isProduction =
    hostname.includes("azurestaticapps.net") ||
    hostname === "sutra.vedprakash.net";
  const isLocalDevelopment = hostname === "localhost";
  const isCustomDomain = hostname === "sutra.vedprakash.net";

  return {
    isProduction,
    isLocalDevelopment,
    isCustomDomain,
    hostname,
  };
};

// Microsoft Entra ID Default Tenant Configuration (Simplified Authentication)
export const AUTH_CONSTANTS = {
  TENANT_ID: "common", // Use common for default tenant access
  CLIENT_ID:
    import.meta.env.VITE_ENTRA_CLIENT_ID ||
    "00000000-0000-0000-0000-000000000000", // App registration for default tenant
  AUTHORITY: "https://login.microsoftonline.com/common",
  SCOPES: ["openid", "profile", "email", "offline_access"] as string[],
  ISSUER: "https://login.microsoftonline.com/common/v2.0",
} as const;

// API Configuration
export const getApiConfig = () => {
  const env = getEnvironmentInfo();

  return {
    baseUrl: env.isProduction
      ? "https://sutra-flex-api-hvyqgbrvnx4ii.azurewebsites.net/api" // Updated to use Flex Function App
      : "/api", // Vite proxy handles local routing
    timeout: 30000,
    retryAttempts: 3,
  };
};

// MSAL Configuration
export const getMSALConfig = (): Configuration => {
  return {
    auth: {
      clientId: AUTH_CONSTANTS.CLIENT_ID,
      authority: AUTH_CONSTANTS.AUTHORITY,
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
          if (containsPii) {
            return;
          }
          switch (level) {
            case 0: // LogLevel.Error
              console.error(message);
              break;
            case 1: // LogLevel.Warning
              console.warn(message);
              break;
            case 2: // LogLevel.Info
              console.info(message);
              break;
            case 3: // LogLevel.Verbose
              console.debug(message);
              break;
            default:
              console.log(message);
              break;
          }
        },
        piiLoggingEnabled: false,
      },
    },
  };
};

// Token Request Configurations
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

// Application Configuration
export const getAppConfig = () => {
  const env = getEnvironmentInfo();

  return {
    // Environment info
    environment: env.isProduction ? "production" : "development",
    ...env,

    // Feature flags
    features: {
      enableGuestMode: true,
      enableMockAuth: !env.isProduction,
      enableAnalytics: env.isProduction,
      enableDebugMode: !env.isProduction,
    },

    // API configuration
    api: getApiConfig(),

    // Authentication configuration
    auth: {
      mode: "msal" as const,
      ...AUTH_CONSTANTS,
    },

    // Application settings
    app: {
      name: "Sutra Multi-LLM Prompt Studio",
      version: "1.0.0",
      description: "Weaving your AI solutions",
    },
  };
};

// Configuration validation
export const validateConfig = (): boolean => {
  const config = getAppConfig();

  // Validate required authentication settings
  if (!config.auth.CLIENT_ID || !config.auth.TENANT_ID) {
    console.error("Missing required authentication configuration");
    return false;
  }

  // Validate API configuration
  if (!config.api.baseUrl) {
    console.error("Missing API base URL configuration");
    return false;
  }

  return true;
};

// Legacy compatibility exports (to be removed after migration)
export const msalConfig = getMSALConfig();
export const loginRequest = getLoginRequestConfig();
export const silentRequest = getSilentTokenRequestConfig();
export const getAuthMode = () => "msal" as const;

// Primary export
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
