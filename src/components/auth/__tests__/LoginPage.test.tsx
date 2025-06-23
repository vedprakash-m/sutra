import { render, screen, fireEvent } from "@testing-library/react";
import LoginPage from "../LoginPage";

// Mock the useAuth hook
const mockLogin = jest.fn();
const mockUseAuth = jest.fn();

jest.mock("../AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoading: false,
    });
  });

  it("should render login page with title and subtitle", () => {
    render(<LoginPage />);

    expect(screen.getByText("Welcome to Sutra")).toBeInTheDocument();
    expect(
      screen.getByText("Multi-LLM Prompt Studio for AI Operations"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Beta Version - Secure Azure AD Authentication"),
    ).toBeInTheDocument();
  });

  it("should render authentication content", () => {
    render(<LoginPage />);

    expect(
      screen.getByText("Secure Authentication Required"),
    ).toBeInTheDocument();

    // In test environment (NODE_ENV=test), expect development mode text
    expect(
      screen.getByText(
        "Development Mode: Sign in with demo credentials or Microsoft account",
      ),
    ).toBeInTheDocument();

    // Check for development mode sign in button
    const signInButton = screen.getByRole("button", {
      name: /Sign in.*Development Mode/i,
    });
    expect(signInButton).toBeInTheDocument();
  });

  it("should call login when sign in button is clicked", () => {
    render(<LoginPage />);

    const signInButton = screen.getByRole("button", {
      name: /Sign in.*Microsoft|Sign in.*Development Mode/i,
    });
    fireEvent.click(signInButton);

    expect(mockLogin).toHaveBeenCalledTimes(1);
  });

  it("should show loading state when isLoading is true", () => {
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoading: true,
    });

    render(<LoginPage />);

    // The button should still be rendered but may be disabled
    const signInButton = screen.getByRole("button", {
      name: /Sign in.*Microsoft|Sign in.*Development Mode/i,
    });
    expect(signInButton).toBeInTheDocument();
  });

  it("should display security and beta notices", () => {
    render(<LoginPage />);

    expect(
      screen.getByText(/Your data is protected with enterprise-grade security/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Beta testing program - help us improve Sutra/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Questions\? Contact support for assistance/),
    ).toBeInTheDocument();
  });

  it("should not crash when login function is undefined", () => {
    mockUseAuth.mockReturnValue({
      login: undefined,
      isLoading: false,
    });

    expect(() => render(<LoginPage />)).not.toThrow();
  });

  it("should render authentication content in production mode", () => {
    // Mock production environment
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "production";

    // Mock window.location for production hostname
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      writable: true,
      value: {
        ...originalLocation,
        hostname: "zealous-flower-04bbe021e.2.azurestaticapps.net",
      },
    });

    render(<LoginPage />);

    expect(
      screen.getByText("Secure Authentication Required"),
    ).toBeInTheDocument();

    // In production mode, expect production text
    expect(
      screen.getByText(
        "Sign in with your Microsoft account to access the Sutra platform",
      ),
    ).toBeInTheDocument();

    // Check for Microsoft sign in button (no development mode)
    const signInButton = screen.getByRole("button", {
      name: /Sign in with Microsoft/i,
    });
    expect(signInButton).toBeInTheDocument();

    // Should not have demo mode role selection
    expect(
      screen.queryByText("Development Mode - Select Role:"),
    ).not.toBeInTheDocument();

    // Restore environment
    process.env.NODE_ENV = originalEnv;
    Object.defineProperty(window, "location", {
      writable: true,
      value: originalLocation,
    });
  });
});
