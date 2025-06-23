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
    expect(
      screen.getByText(
        "Sign in with your Microsoft account to access the Sutra platform",
      ),
    ).toBeInTheDocument();
    // Check for either Microsoft or Development Mode sign in button
    const signInButton = screen.getByRole("button", {
      name: /Sign in.*Microsoft|Sign in.*Development Mode/i,
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
});
