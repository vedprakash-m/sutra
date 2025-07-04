/**
 * Authentication Configuration - Unified Entra ID Implementation
 *
 * This configuration eliminates the dual authentication paradigm and implements
 * consistent Entra ID authentication across all environments per Apps_Auth_Requirement.md
 */

import { PublicClientApplication } from "@azure/msal-browser";
import { getMSALConfig, getLoginRequestConfig, getSilentTokenRequestConfig } from "./index";

// Use the unified configuration
const msalConfig = getMSALConfig();

// Create MSAL instance
export const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL
export const ensureMsalInitialized = async (): Promise<void> => {
  if (!msalInstance.getActiveAccount()) {
    await msalInstance.initialize();
  }
};

// Login request configuration
export const loginRequest = getLoginRequestConfig();

// Silent token request configuration
export const silentRequest = getSilentTokenRequestConfig();

// Authentication mode - always use MSAL for consistent behavior
export const getAuthMode = (): "msal" => {
  return "msal";
};

// Initialize MSAL on module load
ensureMsalInitialized().catch(console.error);

export default {
  msalInstance,
  loginRequest,
  silentRequest,
  getAuthMode,
  ensureMsalInitialized,
};
