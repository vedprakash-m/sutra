import { render, screen, fireEvent } from "@testing-library/react";
import AdminPanel from "../AdminPanel";
import { adminApi } from "@/services/api";

// Mock the API
jest.mock("@/services/api", () => ({
  adminApi: {
    getSystemHealth: jest.fn(),
    getUsageStats: jest.fn(),
    getLLMSettings: jest.fn(),
  },
}));

// Mock useAuth hook
const mockUseAuth = jest.fn();
jest.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock useApi hook
const mockUseApi = jest.fn();
jest.mock("@/hooks/useApi", () => ({
  useApi: () => mockUseApi(),
}));

const mockSystemHealth = {
  status: "healthy",
  uptime: "24h 30m",
  memory: "2.1GB / 4GB",
  cpu: "45%",
  database: "connected",
};

const mockUsageStats = {
  totalUsers: 150,
  activeUsers: 45,
  totalPrompts: 1250,
  totalExecutions: 5600,
};

const mockLLMSettings = {
  providers: [
    { name: "OpenAI", status: "connected", apiKey: "sk-***" }, // pragma: allowlist secret
    { name: "Anthropic", status: "disconnected", apiKey: "" },
  ],
};

describe("AdminPanel", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApi.mockReturnValue({ data: null, loading: false });
    (adminApi.getSystemHealth as jest.Mock).mockResolvedValue(mockSystemHealth);
    (adminApi.getUsageStats as jest.Mock).mockResolvedValue(mockUsageStats);
    (adminApi.getLLMSettings as jest.Mock).mockResolvedValue(mockLLMSettings);
  });

  it("should show access denied for non-admin users", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: false,
      user: { id: "user1", email: "user@example.com" },
    });

    render(<AdminPanel />);

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(
      screen.getByText(
        "You do not have administrative privileges to access this page.",
      ),
    ).toBeInTheDocument();
  });

  it("should render admin panel for admin users", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    expect(screen.getByText("Admin Panel")).toBeInTheDocument();
    expect(
      screen.getByText("Manage system settings, users, and LLM configurations"),
    ).toBeInTheDocument();
  });

  it("should render tab navigation", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("LLM Settings")).toBeInTheDocument();
    expect(screen.getByText("User Management")).toBeInTheDocument();
    expect(screen.getByText("System Health")).toBeInTheDocument();
  });

  it("should switch tabs when clicked", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    // Click on LLM Settings tab
    const llmTab = screen.getByText("LLM Settings");
    fireEvent.click(llmTab);

    // Should show LLM settings content
    expect(screen.getByText("LLM Provider Configuration")).toBeInTheDocument();
  });

  it("should display system health information", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    // Overview tab should be active by default and show Total Users
    expect(screen.getByText("Total Users")).toBeInTheDocument();
  });

  it("should display usage statistics", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    expect(screen.getByText("Monthly Usage")).toBeInTheDocument();
    expect(screen.getByText("Total Prompts")).toBeInTheDocument();
  });

  it("should display loading states", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    // Mock loading state
    mockUseApi.mockReturnValue({ data: null, loading: true });

    render(<AdminPanel />);

    expect(screen.getAllByText("...")).toHaveLength(3); // Should have 3 loading indicators
  });

  it("should handle LLM settings tab", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    const llmTab = screen.getByText("LLM Settings");
    fireEvent.click(llmTab);

    expect(screen.getByText("LLM Provider Configuration")).toBeInTheDocument();
  });

  it("should handle user management tab", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    const usersTab = screen.getByText("User Management");
    fireEvent.click(usersTab);

    expect(
      screen.getByText("User management features coming soon..."),
    ).toBeInTheDocument();
  });

  it("should handle system tab", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    const systemTab = screen.getByText("System Health");
    fireEvent.click(systemTab);

    expect(screen.getByText("System Status")).toBeInTheDocument();
  });

  it("should highlight active tab", () => {
    mockUseAuth.mockReturnValue({
      isAdmin: true,
      user: { id: "admin1", email: "admin@example.com" },
    });

    render(<AdminPanel />);

    // Overview should be active by default
    const overviewTab = screen.getByText("Overview");
    expect(overviewTab.closest("button")).toHaveClass(
      "border-indigo-500",
      "text-indigo-600",
    );
  });
});
