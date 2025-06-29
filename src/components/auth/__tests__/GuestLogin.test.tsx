import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { GuestLogin, GuestUsageIndicator } from "../GuestLogin";
import { useAuth } from "../AuthProvider";

// Mock the AuthProvider
jest.mock("../AuthProvider", () => ({
  useAuth: jest.fn(),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe("GuestLogin Component", () => {
  const mockLoginAsGuest = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      loginAsGuest: mockLoginAsGuest,
      isLoading: false,
      isGuest: false,
      guestSession: null,
      user: null,
      token: null,
      logout: jest.fn(),
      isAuthenticated: false,
      login: jest.fn(),
      isAdmin: false,
    });
  });

  describe("GuestLogin", () => {
    it("renders guest login component with features list", () => {
      render(<GuestLogin />);

      expect(screen.getByText("Try Sutra as a Guest")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Test our AI tools with limited usage - no signup required!",
        ),
      ).toBeInTheDocument();
      expect(screen.getByText("Guest Features:")).toBeInTheDocument();
      expect(screen.getByText("• 5 AI prompts per day")).toBeInTheDocument();
      expect(screen.getByText("• 10 prompt templates")).toBeInTheDocument();
      expect(
        screen.getByText("• 3 collections per session"),
      ).toBeInTheDocument();
      expect(screen.getByText("• 2 playbooks per session")).toBeInTheDocument();
      expect(
        screen.getByText("• 24-hour session duration"),
      ).toBeInTheDocument();
      expect(screen.getByText("Start as Guest")).toBeInTheDocument();
    });

    it("handles guest login when button is clicked", async () => {
      mockLoginAsGuest.mockResolvedValue(undefined);

      render(<GuestLogin />);

      const loginButton = screen.getByText("Start as Guest");
      fireEvent.click(loginButton);

      expect(mockLoginAsGuest).toHaveBeenCalledTimes(1);
      expect(screen.getByText("Starting Guest Session...")).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText("Start as Guest")).toBeInTheDocument();
      });
    });

    it("shows loading state when isLoading is true", () => {
      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest,
        isLoading: true,
        isGuest: false,
        guestSession: null,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
      });

      render(<GuestLogin />);

      const loginButton = screen.getByText("Start as Guest");
      expect(loginButton).toBeDisabled();
    });

    it("disables button during guest login process", async () => {
      let resolveLogin: () => void;
      const loginPromise = new Promise<void>((resolve) => {
        resolveLogin = resolve;
      });
      mockLoginAsGuest.mockReturnValue(loginPromise);

      render(<GuestLogin />);

      const loginButton = screen.getByText("Start as Guest");
      fireEvent.click(loginButton);

      expect(loginButton).toBeDisabled();
      expect(screen.getByText("Starting Guest Session...")).toBeInTheDocument();

      // Resolve the login
      resolveLogin!();
      await waitFor(() => {
        expect(screen.getByText("Start as Guest")).toBeInTheDocument();
      });
    });

    it("handles guest login error gracefully", async () => {
      const consoleErrorSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});
      mockLoginAsGuest.mockRejectedValue(new Error("Login failed"));

      render(<GuestLogin />);

      const loginButton = screen.getByText("Start as Guest");
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "Guest login failed:",
          expect.any(Error),
        );
        expect(screen.getByText("Start as Guest")).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it("displays signup prompt", () => {
      render(<GuestLogin />);

      expect(screen.getByText("Want unlimited access?")).toBeInTheDocument();
      expect(screen.getByText("Sign up for free")).toBeInTheDocument();
    });
  });

  describe("GuestUsageIndicator", () => {
    it("returns null when user is not a guest", () => {
      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest,
        isLoading: false,
        isGuest: false,
        guestSession: null,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
      });

      const { container } = render(<GuestUsageIndicator />);
      expect(container.firstChild).toBeNull();
    });

    it("returns null when guestSession is null", () => {
      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest,
        isLoading: false,
        isGuest: true,
        guestSession: null,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
      });

      const { container } = render(<GuestUsageIndicator />);
      expect(container.firstChild).toBeNull();
    });

    it("displays usage indicator for guest user", () => {
      const mockGuestSession = {
        id: "guest-123",
        active: true,
        usage: {
          llm_calls: 2,
          prompts_created: 5,
        },
        limits: {
          llm_calls_per_day: 5,
          prompts_per_day: 10,
        },
        remaining: {
          llm_calls: 3,
          prompts: 5,
        },
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest,
        isLoading: false,
        isGuest: true,
        guestSession: mockGuestSession,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
      });

      render(<GuestUsageIndicator />);

      expect(screen.getByText("Guest Mode")).toBeInTheDocument();
      expect(screen.getByText("Session Active")).toBeInTheDocument();
      expect(screen.getByText("AI Calls:")).toBeInTheDocument();
      expect(screen.getByText("2 / 5")).toBeInTheDocument();
      expect(screen.getByText("Prompts:")).toBeInTheDocument();
      expect(screen.getByText("5 / 10")).toBeInTheDocument();
    });

    it("displays warning when approaching limit", () => {
      const mockGuestSession = {
        id: "guest-123",
        active: true,
        usage: {
          llm_calls: 4,
          prompts_created: 8,
        },
        limits: {
          llm_calls_per_day: 5,
          prompts_per_day: 10,
        },
        remaining: {
          llm_calls: 1,
          prompts: 2,
        },
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest,
        isLoading: false,
        isGuest: true,
        guestSession: mockGuestSession,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
      });

      render(<GuestUsageIndicator />);

      expect(
        screen.getByText("⚠️ Almost at your daily limit!"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Sign up for unlimited access."),
      ).toBeInTheDocument();
    });

    it("displays warning when at limit", () => {
      const mockGuestSession = {
        id: "guest-123",
        active: true,
        usage: {
          llm_calls: 5,
          prompts_created: 10,
        },
        limits: {
          llm_calls_per_day: 5,
          prompts_per_day: 10,
        },
        remaining: {
          llm_calls: 0,
          prompts: 0,
        },
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest,
        isLoading: false,
        isGuest: true,
        guestSession: mockGuestSession,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
      });

      render(<GuestUsageIndicator />);

      expect(
        screen.getByText("⚠️ Almost at your daily limit!"),
      ).toBeInTheDocument();
    });

    it("handles missing usage data gracefully", () => {
      const mockGuestSession = {
        id: "guest-123",
        active: true,
        usage: {},
        limits: {},
        remaining: {},
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest,
        isLoading: false,
        isGuest: true,
        guestSession: mockGuestSession,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
      });

      render(<GuestUsageIndicator />);

      expect(screen.getByText("0 / 5")).toBeInTheDocument(); // Default fallback values
      expect(screen.getByText("0 / 10")).toBeInTheDocument();
    });
  });
});
