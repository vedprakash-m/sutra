// Mock for @azure/msal-react in Jest environment

import React from "react";

export const MsalProvider = ({ children }: { children: React.ReactNode }) => {
  return <div data-testid="msal-provider">{children}</div>;
};

export const useMsal = () => ({
  instance: {
    loginPopup: jest.fn(),
    logoutPopup: jest.fn(),
    acquireTokenSilent: jest.fn(),
    addEventCallback: jest.fn(),
    removeEventCallback: jest.fn(),
    getActiveAccount: jest.fn(),
    getAllAccounts: jest.fn(() => []),
  },
  accounts: [],
  inProgress: "none",
});

export const useAccount = () => null;

export const useIsAuthenticated = () => false;

export const AuthenticatedTemplate = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  return <div data-testid="authenticated-template">{children}</div>;
};

export const UnauthenticatedTemplate = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  return <div data-testid="unauthenticated-template">{children}</div>;
};

export const useMsalAuthentication = () => ({
  login: jest.fn(),
  result: null,
  error: null,
});
