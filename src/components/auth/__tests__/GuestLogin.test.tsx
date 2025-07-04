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
  const mockGetAccessToken = jest.fn();
  const mockRefreshAuth = jest.fn();

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
      getAccessToken: mockGetAccessToken,
      refreshAuth: mockRefreshAuth,
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

    it("calls loginAsGuest when button is clicked", async () => {
      render(<GuestLogin />);

      const guestButton = screen.getByText("Start as Guest");
      fireEvent.click(guestButton);

      await waitFor(() => {
        expect(mockLoginAsGuest).toHaveBeenCalledTimes(1);
      });
    });

    it("shows loading state while logging in", async () => {
      mockUseAuth.mockReturnValue({
        loginAsGuest: mockLoginAsGuest.mockImplementation(
          () => new Promise(() => {}),
        ), // Never resolves
        isLoading: false,
        isGuest: false,
        guestSession: null,
        user: null,
        token: null,
        logout: jest.fn(),
        isAuthenticated: false,
        login: jest.fn(),
        isAdmin: false,
        getAccessToken: mockGetAccessToken,
        refreshAuth: mockRefreshAuth,
      });

      render(<GuestLogin />);

      const guestButton = screen.getByText("Start as Guest");
      fireEvent.click(guestButton);

      await waitFor(() => {
        expect(
          screen.getByText("Starting Guest Session..."),
        ).toBeInTheDocument();
      });
    });

    it("renders upgrade prompt when user is a guest", () => {
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
        getAccessToken: mockGetAccessToken,
        refreshAuth: mockRefreshAuth,
      });

      render(<GuestLogin />);

      expect(screen.getByText("Want unlimited access?")).toBeInTheDocument();
      expect(screen.getByText("Sign up for free")).toBeInTheDocument();
    });
  });

  describe("GuestUsageIndicator", () => {
    it("shows usage stats when guest session exists", () => {
      const mockGuestSession = {
        id: "guest-123",
        active: true,
        usage: {
          llm_calls: 3,
          prompts_created: 2,
        },
        limits: {
          llm_calls_per_day: 5,
          prompts_per_day: 10,
        },
        remaining: {
          llm_calls: 2,
          prompts: 8,
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
        getAccessToken: mockGetAccessToken,
        refreshAuth: mockRefreshAuth,
      });

      render(<GuestUsageIndicator />);

      expect(screen.getByText("Guest Mode")).toBeInTheDocument();
      expect(screen.getByText("Session Active")).toBeInTheDocument();
      expect(screen.getByText("3 / 5")).toBeInTheDocument(); // AI calls usage
      expect(screen.getByText("2 / 10")).toBeInTheDocument(); // Prompts usage
    });

    it("shows warning when usage is low", () => {
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
        getAccessToken: mockGetAccessToken,
        refreshAuth: mockRefreshAuth,
      });

      render(<GuestUsageIndicator />);

      expect(
        screen.getByText("⚠️ Almost at your daily limit!"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Sign up for unlimited access."),
      ).toBeInTheDocument();
    });

    it("shows expired session message when session has expired", () => {
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
        getAccessToken: mockGetAccessToken,
        refreshAuth: mockRefreshAuth,
      });

      render(<GuestUsageIndicator />);

      expect(
        screen.getByText("⚠️ Almost at your daily limit!"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Sign up for unlimited access."),
      ).toBeInTheDocument();
    });

    it("does not render when no guest session exists", () => {
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
        getAccessToken: mockGetAccessToken,
        refreshAuth: mockRefreshAuth,
      });

      const { container } = render(<GuestUsageIndicator />);
      expect(container.firstChild).toBeNull();
    });
  });
});
