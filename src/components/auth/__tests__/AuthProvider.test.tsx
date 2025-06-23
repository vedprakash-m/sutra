import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { AuthProvider, useAuth } from "../AuthProvider";

// Mock fetch for Static Web Apps auth endpoint
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Helper component to test auth context
function TestComponent() {
  const { user, isAuthenticated, login, logout, isAdmin } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? "authenticated" : "not authenticated"}
      </div>
      <div data-testid="user-info">
        {user ? `${user.name} (${user.email})` : "No user"}
      </div>
      <div data-testid="admin-status">{isAdmin ? "admin" : "not admin"}</div>
      <button onClick={login}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Mock window.location for redirects
    delete (window as any).location;
    (window as any).location = {
      href: "",
      hostname: "localhost", // Mock hostname to prevent undefined errors
    };
  });

  it("renders children and provides auth context", () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ clientPrincipal: null }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    expect(screen.getByTestId("auth-status")).toBeInTheDocument();
  });

  it("handles unauthenticated state", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ clientPrincipal: null }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not authenticated",
      );
      expect(screen.getByTestId("user-info")).toHaveTextContent("No user");
      expect(screen.getByTestId("admin-status")).toHaveTextContent("not admin");
    });
  });

  it("handles authenticated user state", async () => {
    const mockUser = {
      identityProvider: "aad",
      userId: "test-user-id",
      userDetails: "test@example.com",
      userRoles: ["user"], // Azure AD still uses array
      claims: [
        {
          typ: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
          val: "test@example.com",
        },
        {
          typ: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
          val: "Test User",
        },
      ],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ clientPrincipal: mockUser }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated",
      );
      expect(screen.getByTestId("user-info")).toHaveTextContent(
        "Test User (test@example.com)",
      );
      expect(screen.getByTestId("admin-status")).toHaveTextContent("not admin");
    });
  });

  it("handles admin user state", async () => {
    const mockAdminUser = {
      identityProvider: "aad",
      userId: "admin-user-id",
      userDetails: "admin@example.com",
      userRoles: ["admin"], // Admin role in Azure AD userRoles
      claims: [
        {
          typ: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
          val: "admin@example.com",
        },
        {
          typ: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
          val: "Admin User",
        },
      ],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ clientPrincipal: mockAdminUser }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated",
      );
      expect(screen.getByTestId("user-info")).toHaveTextContent(
        "Admin User (admin@example.com)",
      );
      expect(screen.getByTestId("admin-status")).toHaveTextContent("admin");
    });
  });

  it("redirects to login when login button is clicked", async () => {
    // Mock Azure Static Web Apps hostname to trigger redirect behavior
    (window as any).location.hostname = "app.azurestaticapps.net";

    // Mock window.alert to avoid JSDOM error
    const mockAlert = jest.fn();
    global.alert = mockAlert;

    // Mock /.auth/me endpoint to return no user during AuthProvider initialization
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ clientPrincipal: null }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Wait for initial auth check to complete
    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not authenticated",
      );
    });

    // Reset fetch mock for login flow
    mockFetch.mockClear();

    // Mock the login flow:
    // 1. /.auth/me check (successful)
    mockFetch.mockResolvedValueOnce({
      ok: true,
    });

    // 2. /.auth/providers check (fails, so fallback to direct provider attempts)
    mockFetch.mockResolvedValueOnce({
      ok: false,
    });

    // 3. HEAD request to /.auth/login/azureActiveDirectory (fails)
    mockFetch.mockResolvedValueOnce({
      status: 404,
    });

    // 4. HEAD request to /.auth/login/aad (succeeds)
    mockFetch.mockResolvedValueOnce({
      status: 200,
    });

    const loginButton = screen.getByText("Login");
    await act(async () => {
      fireEvent.click(loginButton);
    });

    expect(window.location.href).toBe("/.auth/login/aad");
  });

  it("redirects to logout when logout button is clicked", async () => {
    // Mock Azure Static Web Apps hostname to trigger redirect behavior
    (window as any).location.hostname = "app.azurestaticapps.net";

    const mockUser = {
      identityProvider: "aad",
      userId: "test-user-id",
      userDetails: "test@example.com",
      userRoles: ["user"],
      claims: [
        {
          typ: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
          val: "test@example.com",
        },
      ],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ clientPrincipal: mockUser }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated",
      );
    });

    fireEvent.click(screen.getByText("Logout"));
    expect(window.location.href).toBe("/.auth/logout");
  });

  it("handles fetch errors gracefully", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not authenticated",
      );
      expect(screen.getByTestId("user-info")).toHaveTextContent("No user");
    });
  });
});
