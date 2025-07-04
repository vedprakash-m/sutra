import React from "react";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@/components/auth/MSALAuthProvider";
import Dashboard from "@/components/dashboard/Dashboard";

// Mock the API services first
jest.mock("@/services/api", () => ({
  collectionsApi: {
    getCollections: jest.fn(),
    createCollection: jest.fn(),
    updateCollection: jest.fn(),
    deleteCollection: jest.fn(),
  },
  playbooksApi: {
    getPlaybooks: jest.fn(),
    createPlaybook: jest.fn(),
    updatePlaybook: jest.fn(),
    deletePlaybook: jest.fn(),
  },
}));

// Mock the useAuth hook to return unauthenticated state
jest.mock("@/components/auth/AuthProvider", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: jest.fn(),
    logout: jest.fn(),
    isAdmin: false,
  }),
}));

describe("Dashboard", () => {
  it("should render welcome message when not authenticated", () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>,
    );

    expect(screen.getByText("Welcome back,")).toBeInTheDocument();
    expect(
      screen.getByText("Here's what you can do with Sutra today"),
    ).toBeInTheDocument();
  });
});
