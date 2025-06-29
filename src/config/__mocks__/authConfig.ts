// Mock MSAL configuration for Jest testing environment

export const msalConfig = {
  auth: {
    clientId: "00000000-0000-0000-0000-000000000000",
    authority: "https://login.microsoftonline.com/common",
    redirectUri: "http://localhost:3000",
    postLogoutRedirectUri: "http://localhost:3000",
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
};

export const msalInstance = {
  loginPopup: jest.fn(),
  logoutPopup: jest.fn(),
  acquireTokenSilent: jest.fn(),
  addEventCallback: jest.fn(),
  removeEventCallback: jest.fn(),
};

export const loginRequest = {
  scopes: ["openid", "profile", "email", "User.Read"],
};

export const silentRequest = {
  scopes: ["openid", "profile", "email", "User.Read"],
  account: undefined,
};

export const getAuthMode = () => "mock";
