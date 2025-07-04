// Production runtime configuration aligned with Apps_Auth_Requirement.md
// This file provides configuration that works in production without build-time env vars

const isCustomDomain = window.location.hostname === "sutra.vedprakash.net";
const isProd =
  window.location.hostname.includes("azurestaticapps.net") || isCustomDomain;

export const getConfig = () => {
  if (isProd) {
    return {
      // Vedprakash Domain Authentication Standards (Apps_Auth_Requirement.md)
      clientId: "db1e3417-e353-4255-b05e-2e1fffe25692",
      tenantId: "80fe68b7-105c-4fb9-ab03-c9a818e35848", // vedid.onmicrosoft.com
      redirectUri: window.location.origin,
      authority:
        "https://login.microsoftonline.com/80fe68b7-105c-4fb9-ab03-c9a818e35848",
      apiBaseUrl: "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api",
      useLocalApi: false,
      enableGuestMode: true,
      enableMockAuth: false,
      // Vedprakash domain-specific settings
      vedprakashDomain: true,
      customDomain: isCustomDomain,
    };
  }

  // Development fallback
  return {
    clientId: "00000000-0000-0000-0000-000000000000",
    tenantId: "80fe68b7-105c-4fb9-ab03-c9a818e35848",
    redirectUri: window.location.origin,
    authority:
      "https://login.microsoftonline.com/80fe68b7-105c-4fb9-ab03-c9a818e35848",
    apiBaseUrl: "/api",
    useLocalApi: true,
    enableGuestMode: true,
    enableMockAuth: true,
  };
};
