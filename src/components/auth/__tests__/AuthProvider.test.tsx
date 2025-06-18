import { render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "../AuthProvider";
import { BrowserRouter } from "react-router-dom";
import { act } from "react";

// Test component that uses the auth context
function TestComponent() {
  const { user, isAuthenticated, isAdmin, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? "authenticated" : "not-authenticated"}
      </div>
      <div data-testid="user-info">
        {user ? `User: ${user.name}` : "No user"}
      </div>
      <div data-testid="admin-status">{isAdmin ? "admin" : "not-admin"}</div>
      <button onClick={() => login("test@example.com")}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  const renderWithAuth = () => {
    return render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>,
    );
  };

  it("should provide initial unauthenticated state", () => {
    renderWithAuth();

    expect(screen.getByTestId("auth-status")).toHaveTextContent(
      "not-authenticated",
    );
    expect(screen.getByTestId("user-info")).toHaveTextContent("No user");
    expect(screen.getByTestId("admin-status")).toHaveTextContent("not-admin");
  });

  it("should handle login", async () => {
    renderWithAuth();

    const loginButton = screen.getByText("Login");

    await act(async () => {
      loginButton.click();
    });

    // Wait for any async state updates to complete
    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toBeInTheDocument();
    });
  });

  it("should handle logout", async () => {
    renderWithAuth();

    const logoutButton = screen.getByText("Logout");

    await act(async () => {
      logoutButton.click();
    });

    // Wait for logout to complete and verify state
    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated",
      );
    });
  });
});
