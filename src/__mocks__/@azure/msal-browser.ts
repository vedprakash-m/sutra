// Mock for @azure/msal-browser in Jest environment

export class PublicClientApplication {
  constructor(_config: any) {}

  initialize = jest.fn().mockResolvedValue(undefined);
  loginPopup = jest.fn();
  loginRedirect = jest.fn();
  logoutPopup = jest.fn();
  logoutRedirect = jest.fn();
  acquireTokenSilent = jest.fn();
  acquireTokenPopup = jest.fn();
  addEventCallback = jest.fn();
  removeEventCallback = jest.fn();
  getActiveAccount = jest.fn();
  getAllAccounts = jest.fn(() => []);
}

export const EventType = {
  LOGIN_SUCCESS: "msal:loginSuccess",
  LOGIN_FAILURE: "msal:loginFailure",
  LOGOUT_SUCCESS: "msal:logoutSuccess",
  LOGOUT_FAILURE: "msal:logoutFailure",
};

export interface Configuration {
  auth: {
    clientId: string;
    authority?: string;
    redirectUri?: string;
    postLogoutRedirectUri?: string;
  };
  cache?: any;
  system?: any;
}

export interface AccountInfo {
  homeAccountId: string;
  localAccountId: string;
  username: string;
  name?: string;
  tenantId?: string;
  idTokenClaims?: any;
}

export interface EventMessage {
  eventType: string;
  interactionType?: string;
  payload?: any;
  error?: any;
  timestamp: number;
}
