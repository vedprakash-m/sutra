import { render, screen } from "@testing-library/react";
import { ReactNode } from "react";
import IntegrationsPage from "../IntegrationsPage";

// Mock the integrationsApi before importing
jest.mock("@/services/api", () => ({
  integrationsApi: {
    listLLM: jest.fn().mockResolvedValue({
      integrations: {},
      supportedProviders: [],
    }),
    saveLLM: jest.fn().mockResolvedValue({}),
    deleteLLM: jest.fn().mockResolvedValue({}),
  },
}));

// Mock user for regular user tests
const mockRegularUser = {
  id: "test-user-1",
  email: "test@example.com",
  name: "Test User",
  givenName: "Test",
  familyName: "User",
  permissions: ["user"],
  vedProfile: {
    profileId: "test-user-1",
    subscriptionTier: "free" as const,
    appsEnrolled: ["sutra"],
    preferences: {},
  },
};

// Mock user for admin tests
const mockAdminUser = {
  id: "admin-user-1",
  email: "admin@example.com",
  name: "Admin User",
  givenName: "Admin",
  familyName: "User",
  permissions: ["admin"],
  vedProfile: {
    profileId: "admin-user-1",
    subscriptionTier: "free" as const,
    appsEnrolled: ["sutra"],
    preferences: {},
  },
};

// Mock the useAuth hook
const mockUseAuth = jest.fn();

jest.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
  AuthProvider: ({ children }: { children: ReactNode }) => children,
}));

describe("IntegrationsPage", () => {
  beforeEach(() => {
    // Default to regular user
    mockUseAuth.mockReturnValue({
      user: mockRegularUser,
      isAuthenticated: true,
      isGuest: false,
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      isAdmin: false,
      token: "test-token",
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });
  it("should render the integrations page with title", () => {
    render(<IntegrationsPage />);

    expect(screen.getByText("Integrations")).toBeInTheDocument();
    expect(
      screen.getByText("Connect to LLM providers and external services"),
    ).toBeInTheDocument();
  });

  it("should display integration cards", () => {
    render(<IntegrationsPage />);

    // Check for integration names
    expect(screen.getByText("OpenAI GPT")).toBeInTheDocument();
    expect(screen.getByText("Anthropic Claude")).toBeInTheDocument();
    expect(screen.getByText("Google Gemini")).toBeInTheDocument();
  });

  it("should display integration descriptions", () => {
    render(<IntegrationsPage />);

    expect(
      screen.getByText("Connect to OpenAI's GPT models for text generation"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Connect to Anthropic's Claude models for AI assistance",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Connect to Google's Gemini models for AI capabilities"),
    ).toBeInTheDocument();
  });

  it("should display status badges", () => {
    render(<IntegrationsPage />);

    // All integrations start as disconnected
    const disconnectedElements = screen.getAllByText("disconnected");
    expect(disconnectedElements).toHaveLength(3);
  });

  it("should have configure buttons for each integration", () => {
    render(<IntegrationsPage />);

    const configureButtons = screen.getAllByText("Configure");
    expect(configureButtons).toHaveLength(3);
  });

  it("should apply correct status colors", () => {
    render(<IntegrationsPage />);

    const statusBadges = screen.getAllByText("disconnected");
    statusBadges.forEach((badge) => {
      expect(badge).toHaveClass("bg-gray-100", "text-gray-800");
    });
  });

  it("should render integration cards with proper structure", () => {
    render(<IntegrationsPage />);

    // Check that each integration has the expected structure
    const openAICard = screen.getByText("OpenAI GPT").closest("div");
    expect(openAICard).toBeInTheDocument();

    const claudeCard = screen.getByText("Anthropic Claude").closest("div");
    expect(claudeCard).toBeInTheDocument();

    const geminiCard = screen.getByText("Google Gemini").closest("div");
    expect(geminiCard).toBeInTheDocument();
  });

  it("should show admin configuration required message for regular users", () => {
    render(<IntegrationsPage />);

    expect(screen.getByText("Admin Access Required")).toBeInTheDocument();
    expect(
      screen.getByText(
        "LLM integrations are managed by administrators. Contact your admin to configure API keys and budgets.",
      ),
    ).toBeInTheDocument();
  });

  it("should show admin dashboard for admin users", () => {
    // Mock admin user for this test
    mockUseAuth.mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isGuest: false,
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      isAdmin: true,
      token: "admin-token",
    });

    render(<IntegrationsPage />);

    expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText(
        "You can configure LLM provider API keys and manage system integrations.",
      ),
    ).toBeInTheDocument();
  });
});
