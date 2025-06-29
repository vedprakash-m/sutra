import { Configuration, PublicClientApplication } from "@azure/msal-browser";

// Environment variables helper for Jest compatibility and production
const getEnvVar = (key: string, defaultValue = "") => {
  // Check if we're in Jest environment
  if (typeof process !== "undefined" && process.env.NODE_ENV === "test") {
    return process.env[key] || defaultValue;
  }

  // Check if import.meta is available (Vite environment)
  if (typeof window !== "undefined" && window.location) {
    // In browser with Vite, try to access import.meta safely
    try {
      const importMeta = (globalThis as any).import?.meta;
      if (importMeta && importMeta.env) {
        return importMeta.env[key] || defaultValue;
      }
    } catch {
      // Fallback if import.meta access fails
    }
  }

  // Fallback to process.env
  return (
    (typeof process !== "undefined" ? process.env[key] : undefined) ||
    defaultValue
  );
};

// Get production configuration based on environment
const getProductionConfig = () => {
  const isProduction =
    getEnvVar("NODE_ENV") === "production" ||
    (typeof window !== "undefined" &&
      window.location.hostname.includes("azurestaticapps.net"));

  if (isProduction) {
    // Production configuration from Azure Static Web Apps
    const currentOrigin =
      typeof window !== "undefined"
        ? window.location.origin
        : "https://localhost:5173";
    return {
      clientId: getEnvVar(
        "VITE_ENTRA_CLIENT_ID",
        "61084964-08b8-49ea-b624-4859c4dc37de",
      ), // Fallback to existing
      redirectUri: currentOrigin,
      authority: "https://login.microsoftonline.com/vedid.onmicrosoft.com",
    };
  }

  // Development configuration
  return {
    clientId: getEnvVar(
      "VITE_ENTRA_CLIENT_ID",
      "00000000-0000-0000-0000-000000000000",
    ),
    redirectUri:
      getEnvVar("VITE_ENTRA_REDIRECT_URI") ||
      (typeof window !== "undefined"
        ? window.location.origin
        : "http://localhost:5173"),
    authority: "https://login.microsoftonline.com/vedid.onmicrosoft.com",
  };
};

// MSAL Configuration for Microsoft Entra ID - Apps_Auth_Requirement.md Compliance
const prodConfig = getProductionConfig();

export const msalConfig: Configuration = {
  auth: {
    clientId: prodConfig.clientId,
    authority: prodConfig.authority,
    redirectUri: prodConfig.redirectUri,
    postLogoutRedirectUri:
      typeof window !== "undefined"
        ? window.location.origin
        : "http://localhost:5173",
  },
  cache: {
    cacheLocation: "sessionStorage", // Required for SSO compatibility
    storeAuthStateInCookie: true, // Required for Safari/iOS SSO
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case 0: // Error
            console.error("[MSAL] Error:", message);
            break;
          case 1: // Warning
            console.warn("[MSAL] Warning:", message);
            break;
          case 2: // Info
            console.info("[MSAL] Info:", message);
            break;
          case 3: // Verbose
            console.debug("[MSAL] Verbose:", message);
            break;
        }
      },
      piiLoggingEnabled: false,
    },
  },
};

// Create the MSAL instance
export const msalInstance = new PublicClientApplication(msalConfig);

// Login request configuration
export const loginRequest = {
  scopes: ["openid", "profile", "email", "User.Read"],
};

// Silent token request configuration
export const silentRequest = {
  scopes: ["openid", "profile", "email", "User.Read"],
  account: undefined as any, // Will be set dynamically
};

/**
 * Environment detection for authentication mode - Apps_Auth_Requirement.md Compliance
 */
export const getAuthMode = (): "msal" | "swa" | "mock" => {
  // Check if MSAL configuration is available (priority)
  const hasMsalConfig =
    getEnvVar("VITE_ENTRA_CLIENT_ID") &&
    getEnvVar("VITE_ENTRA_CLIENT_ID") !==
      "00000000-0000-0000-0000-000000000000";

  // Check if we're in Azure Static Web Apps production
  const isAzureStaticWebApps =
    typeof window !== "undefined" &&
    (window.location.hostname.includes("azurestaticapps.net") ||
      window.location.hostname.includes("sutra.vedprakash.net"));

  if (hasMsalConfig) {
    return "msal"; // Required: Microsoft Entra ID authentication
  } else if (isAzureStaticWebApps) {
    return "swa"; // Fallback: Azure Static Web Apps authentication
  } else {
    return "mock"; // Development: Local mock authentication
  }
};
