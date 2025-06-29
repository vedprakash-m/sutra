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

  it("should handle role selection in development mode", () => {
    render(<LoginPage />);

    // Should show role selection in development mode
    expect(
      screen.getByText("Development Mode - Select Role:"),
    ).toBeInTheDocument();

    const userRadio = screen.getByLabelText("Regular User");
    const adminRadio = screen.getByLabelText("Admin User");

    expect(userRadio).toBeChecked();
    expect(adminRadio).not.toBeChecked();

    // Change to admin role
    fireEvent.click(adminRadio);
    expect(adminRadio).toBeChecked();
    expect(userRadio).not.toBeChecked();

    // Change back to user role
    fireEvent.click(userRadio);
    expect(userRadio).toBeChecked();
    expect(adminRadio).not.toBeChecked();
  });

  it("should store role preference and call login in development mode", () => {
    const setItemSpy = jest.spyOn(Storage.prototype, "setItem");

    render(<LoginPage />);

    // Select admin role
    const adminRadio = screen.getByLabelText("Admin User");
    fireEvent.click(adminRadio);

    // Click sign in button
    const signInButton = screen.getByRole("button", {
      name: /Sign in.*Development Mode/i,
    });
    fireEvent.click(signInButton);

    expect(setItemSpy).toHaveBeenCalledWith("sutra_demo_role", "admin");
    expect(mockLogin).toHaveBeenCalledTimes(1);

    setItemSpy.mockRestore();
  });

  describe("Production authentication flow", () => {
    let originalEnv: string | undefined;
    let originalLocation: Location;
    let mockFetch: jest.Mock;

    beforeEach(() => {
      // Setup production environment
      originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "production";

      originalLocation = window.location;
      Object.defineProperty(window, "location", {
        writable: true,
        value: {
          ...originalLocation,
          hostname: "production.example.com",
          href: "",
        },
      });

      // Mock fetch globally
      mockFetch = jest.fn();
      global.fetch = mockFetch;

      // Mock alert
      global.alert = jest.fn();
    });

    afterEach(() => {
      // Restore environment
      process.env.NODE_ENV = originalEnv;
      Object.defineProperty(window, "location", {
        writable: true,
        value: originalLocation,
      });

      jest.restoreAllMocks();
    });

    it("should handle auth system not configured", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(global.alert).toHaveBeenCalledWith(
        "Authentication system is not properly configured.\n\n" +
          "Please contact the administrator to enable authentication in Azure Static Web Apps.",
      );
    });

    it("should redirect to Microsoft provider when found", async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true }) // /.auth/me
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve([{ name: "microsoft" }, { name: "github" }]),
        }); // /.auth/providers

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(window.location.href).toBe("/.auth/login/microsoft");
    });

    it("should redirect to Azure AD provider when found", async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true }) // /.auth/me
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve([
              { name: "azureActiveDirectory" },
              { name: "github" },
            ]),
        }); // /.auth/providers

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(window.location.href).toBe("/.auth/login/azureActiveDirectory");
    });

    it("should try fallback provider names when providers endpoint fails", async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true }) // /.auth/me
        .mockResolvedValueOnce({ ok: false }) // /.auth/providers fails
        .mockResolvedValueOnce({ status: 200 }); // HEAD request for azureActiveDirectory

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(window.location.href).toBe("/.auth/login/azureActiveDirectory");
    });

    it("should try multiple provider names until one works", async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true }) // /.auth/me
        .mockResolvedValueOnce({ ok: false }) // /.auth/providers fails
        .mockResolvedValueOnce({ status: 404 }) // HEAD azureActiveDirectory
        .mockResolvedValueOnce({ status: 404 }) // HEAD aad
        .mockResolvedValueOnce({ status: 200 }); // HEAD microsoft

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(window.location.href).toBe("/.auth/login/microsoft");
    });

    it("should show error when no providers work", async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true }) // /.auth/me
        .mockResolvedValueOnce({ ok: false }) // /.auth/providers fails
        .mockResolvedValueOnce({ status: 404 }) // HEAD azureActiveDirectory
        .mockResolvedValueOnce({ status: 404 }) // HEAD aad
        .mockResolvedValueOnce({ status: 404 }) // HEAD microsoft
        .mockResolvedValueOnce({ status: 404 }); // HEAD azuread

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(global.alert).toHaveBeenCalledWith(
        "Unable to access Microsoft authentication.\n\n" +
          "The authentication system may not be properly configured.\n" +
          "Please contact support.",
      );
    });

    it("should handle network errors during authentication", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(global.alert).toHaveBeenCalledWith(
        "Authentication error. Please check your connection and try again.",
      );
    });

    it("should handle provider request failures gracefully", async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true }) // /.auth/me
        .mockResolvedValueOnce({ ok: false }) // /.auth/providers fails
        .mockRejectedValueOnce(new Error("Network error")) // HEAD azureActiveDirectory
        .mockRejectedValueOnce(new Error("Network error")) // HEAD aad
        .mockResolvedValueOnce({ status: 200 }); // HEAD microsoft

      render(<LoginPage />);

      const signInButton = screen.getByRole("button", {
        name: /Sign in with Microsoft/i,
      });
      fireEvent.click(signInButton);

      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(window.location.href).toBe("/.auth/login/microsoft");
    });
  });
});
