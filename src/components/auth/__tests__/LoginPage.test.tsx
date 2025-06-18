import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "../LoginPage";

// Mock the useAuth hook
const mockLogin = jest.fn();
const mockUseAuth = jest.fn();

jest.mock("./AuthProvider", () => ({
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

    expect(screen.getByText("Sign in to Sutra")).toBeInTheDocument();
    expect(screen.getByText("AI Operations Platform - Development Mode")).toBeInTheDocument();
  });

  it("should render login type options", () => {
    render(<LoginPage />);

    expect(screen.getByText("Login as:")).toBeInTheDocument();
    expect(screen.getByText("Regular User")).toBeInTheDocument();
    expect(screen.getByText("Administrator")).toBeInTheDocument();
  });

  it("should have user option selected by default", () => {
    render(<LoginPage />);

    const userRadio = screen.getByRole("radio", { name: "Regular User" });
    const adminRadio = screen.getByRole("radio", { name: "Administrator" });

    expect(userRadio).toBeChecked();
    expect(adminRadio).not.toBeChecked();
  });

  it("should allow switching between user and admin login types", () => {
    render(<LoginPage />);

    const userRadio = screen.getByRole("radio", { name: "Regular User" });
    const adminRadio = screen.getByRole("radio", { name: "Administrator" });

    // Click admin radio
    fireEvent.click(adminRadio);
    expect(adminRadio).toBeChecked();
    expect(userRadio).not.toBeChecked();

    // Click user radio
    fireEvent.click(userRadio);
    expect(userRadio).toBeChecked();
    expect(adminRadio).not.toBeChecked();
  });

  it("should render sign in button", () => {
    render(<LoginPage />);

    const signInButton = screen.getByRole("button", { name: "Sign in (Development Mode)" });
    expect(signInButton).toBeInTheDocument();
    expect(signInButton).toBeEnabled();
  });

  it("should call login with user email when user login is clicked", async () => {
    render(<LoginPage />);

    const signInButton = screen.getByRole("button", { name: "Sign in (Development Mode)" });
    fireEvent.click(signInButton);

    expect(mockLogin).toHaveBeenCalledWith("user@sutra.ai", false);
  });

  it("should call login with admin email when admin login is clicked", async () => {
    render(<LoginPage />);

    const adminRadio = screen.getByRole("radio", { name: "Administrator" });
    fireEvent.click(adminRadio);

    const signInButton = screen.getByRole("button", { name: "Sign in (Development Mode)" });
    fireEvent.click(signInButton);

    expect(mockLogin).toHaveBeenCalledWith("admin@sutra.ai", true);
  });

  it("should show loading state when isLoading is true", () => {
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoading: true,
    });

    render(<LoginPage />);

    const signInButton = screen.getByRole("button", { name: "Signing in..." });
    expect(signInButton).toBeInTheDocument();
    expect(signInButton).toBeDisabled();
  });

  it("should handle login errors gracefully", async () => {
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    mockLogin.mockRejectedValue(new Error("Login failed"));

    render(<LoginPage />);

    const signInButton = screen.getByRole("button", { name: "Sign in (Development Mode)" });
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith("Login failed:", expect.any(Error));
    });

    consoleErrorSpy.mockRestore();
  });

  it("should display development mode notice", () => {
    render(<LoginPage />);

    expect(screen.getByText(/This is a development environment/)).toBeInTheDocument();
    expect(screen.getByText(/integrate with Azure AD B2C/)).toBeInTheDocument();
  });

  it("should not crash when login function is undefined", () => {
    mockUseAuth.mockReturnValue({
      login: undefined,
      isLoading: false,
    });

    expect(() => render(<LoginPage />)).not.toThrow();
  });
});
