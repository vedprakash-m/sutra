/**
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
