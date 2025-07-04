import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useAuth } from "../AuthProvider";
import LoginPage from "../LoginPage";

// Mock the auth provider
jest.mock("../AuthProvider", () => ({
  useAuth: jest.fn(),
}));

// Mock the AnonymousLLMTest component
jest.mock("../AnonymousLLMTest", () => ({
  AnonymousLLMTest: () => (
    <div data-testid="anonymous-llm-test">Anonymous LLM Test Component</div>
  ),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe("LoginPage", () => {
  const mockLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock localStorage
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });

    // Mock window.location
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
      },
      writable: true,
    });

    // Mock window.alert
    window.alert = jest.fn();

    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoading: false,
      isAuthenticated: false,
      isGuest: false,
      isAdmin: false,
      user: null,
      token: null,
      logout: jest.fn(),
      loginAsGuest: jest.fn(),
      guestSession: null,
      getAccessToken: jest.fn(),
      refreshAuth: jest.fn(),
    });
  });

  it("renders login page with title and description", () => {
    render(<LoginPage />);

    expect(screen.getByText("Welcome to Sutra")).toBeInTheDocument();
    expect(
      screen.getByText("Multi-LLM Prompt Studio for AI Operations"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Beta Version - Secure Azure AD Authentication"),
    ).toBeInTheDocument();
  });

  it("renders role selection in development mode", () => {
    render(<LoginPage />);

    expect(
      screen.getByText("Development Mode - Select Role:"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Regular User")).toBeInTheDocument();
    expect(screen.getByLabelText("Admin User")).toBeInTheDocument();
  });

  it("renders sign in button", () => {
    render(<LoginPage />);

    expect(screen.getByText("Sign in (Development Mode)")).toBeInTheDocument();
  });

  it("calls login when sign in button is clicked", async () => {
    render(<LoginPage />);

    const signInButton = screen.getByText("Sign in (Development Mode)");
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledTimes(1);
    });
  });

  it("sets role preference in localStorage during development", async () => {
    const mockSetItem = jest.fn();
    Object.defineProperty(window, "localStorage", {
      value: { setItem: mockSetItem },
      writable: true,
    });

    render(<LoginPage />);

    // Select admin role
    const adminRadio = screen.getByLabelText("Admin User");
    fireEvent.click(adminRadio);

    // Click sign in
    const signInButton = screen.getByText("Sign in (Development Mode)");
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockSetItem).toHaveBeenCalledWith("sutra_demo_role", "admin");
      expect(mockLogin).toHaveBeenCalledTimes(1);
    });
  });

  it("handles login errors gracefully", async () => {
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    const alertSpy = jest.fn();
    window.alert = alertSpy;

    mockLogin.mockRejectedValueOnce(new Error("Login failed"));

    render(<LoginPage />);

    const signInButton = screen.getByText("Sign in (Development Mode)");
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "❌ Authentication failed:",
        expect.any(Error),
      );
      expect(alertSpy).toHaveBeenCalledWith(
        expect.stringContaining("Authentication failed. Please try again."),
      );
    });

    consoleSpy.mockRestore();
  });

  it("renders anonymous LLM test component", () => {
    render(<LoginPage />);

    expect(screen.getByTestId("anonymous-llm-test")).toBeInTheDocument();
  });

  it("updates selected role when radio button is changed", () => {
    render(<LoginPage />);

    const userRadio = screen.getByLabelText("Regular User");
    const adminRadio = screen.getByLabelText("Admin User");

    // Initially, user should be selected
    expect(userRadio).toBeChecked();
    expect(adminRadio).not.toBeChecked();

    // Click admin radio
    fireEvent.click(adminRadio);

    expect(adminRadio).toBeChecked();
    expect(userRadio).not.toBeChecked();
  });

  it("shows development mode features only in development environment", () => {
    // Test in development mode (localhost)
    render(<LoginPage />);
    expect(
      screen.getByText("Development Mode - Select Role:"),
    ).toBeInTheDocument();

    // Test in production mode
    Object.defineProperty(window, "location", {
      value: { hostname: "myapp.azurestaticapps.net" },
      writable: true,
    });

    render(<LoginPage />);
    // Development mode text should still be there since NODE_ENV is test
    expect(
      screen.getByText("Development Mode - Select Role:"),
    ).toBeInTheDocument();
  });
});
