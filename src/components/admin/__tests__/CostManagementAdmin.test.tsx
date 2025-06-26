import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import CostManagementAdmin from "../CostManagementAdmin";

// Mock the useCostManagement hook
jest.mock("../../../hooks/useCostManagement", () => ({
  __esModule: true,
  default: jest.fn(),
}));

// Mock fetch for API calls
global.fetch = jest.fn();

const mockUseCostManagement =
  require("../../../hooks/useCostManagement").default;
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe("CostManagementAdmin", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();

    mockUseCostManagement.mockReturnValue({
      formatCurrency: jest
        .fn()
        .mockImplementation((val) => `$${val.toFixed(2)}`),
    });
  });

  it("should render loading state initially", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<CostManagementAdmin />);

    // The actual rendered text is "Cost Management", not "Cost Management Dashboard"
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("should render analytics data", async () => {
    const mockAnalytics = {
      systemOverview: {
        totalSpend: 1250.75,
        totalUsers: 125,
        totalExecutions: 5420,
        averageCostPerUser: 10.01,
        period: "monthly",
      },
      topUsers: [
        { userId: "user-1", cost: 103.5, executions: 30 },
        { userId: "user-2", cost: 89.2, executions: 25 },
      ],
      modelUsage: {
        "gpt-4": { usageCount: 150, totalCost: 450.0, avgCost: 3.0 },
        "gpt-3.5-turbo": { usageCount: 300, totalCost: 75.0, avgCost: 0.25 },
      },
      budgetAlerts: {
        activeAlerts: 12,
        criticalAlerts: 3,
        usersOverBudget: 5,
        recentRestrictions: 2,
      },
      costTrends: {
        trendDirection: "increasing",
        growthRate: 15.5,
        seasonalPatterns: ["workdays-high", "weekend-low"],
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalytics,
    } as Response);

    render(<CostManagementAdmin />);

    await waitFor(() => {
      expect(screen.getByText("$1250.75")).toBeInTheDocument(); // Remove comma formatting
      expect(screen.getByText("125")).toBeInTheDocument();
      expect(screen.getByText("5,420")).toBeInTheDocument();
      expect(screen.getByText("$10.01")).toBeInTheDocument();
    });

    expect(screen.getByText("Top Users by Cost")).toBeInTheDocument();
    expect(screen.getByText("user-1")).toBeInTheDocument();
    expect(screen.getByText("$103.50")).toBeInTheDocument();
  });

  it("should handle API error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("API Error"));

    render(<CostManagementAdmin />);

    await waitFor(() => {
      expect(
        screen.getByText("Failed to load cost analytics"),
      ).toBeInTheDocument(); // Correct error message
    });
  });

  it("should allow changing time period", async () => {
    const mockAnalytics = {
      systemOverview: {
        totalSpend: 500.0,
        totalUsers: 50,
        totalExecutions: 2000,
        averageCostPerUser: 10.0,
        period: "weekly",
      },
      topUsers: [],
      modelUsage: {},
      budgetAlerts: {
        activeAlerts: 5,
        criticalAlerts: 1,
        usersOverBudget: 2,
        recentRestrictions: 0,
      },
      costTrends: {
        trendDirection: "stable",
        growthRate: 0,
        seasonalPatterns: [],
      },
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockAnalytics,
    } as Response);

    render(<CostManagementAdmin />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText("$500.00")).toBeInTheDocument();
    });

    // Change time period
    const periodSelector = screen.getByRole("combobox"); // Use role instead of value
    fireEvent.change(periodSelector, { target: { value: "weekly" } });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2); // Initial + after change
    });
  });

  it("should display model usage statistics", async () => {
    const mockAnalytics = {
      systemOverview: {
        totalSpend: 1000.0,
        totalUsers: 100,
        totalExecutions: 4000,
        averageCostPerUser: 10.0,
        period: "monthly",
      },
      topUsers: [],
      modelUsage: {
        "gpt-4": { usageCount: 100, totalCost: 300.0, avgCost: 3.0 },
        "gpt-3.5-turbo": { usageCount: 200, totalCost: 50.0, avgCost: 0.25 },
        "claude-3": { usageCount: 50, totalCost: 150.0, avgCost: 3.0 },
      },
      budgetAlerts: {
        activeAlerts: 8,
        criticalAlerts: 2,
        usersOverBudget: 3,
        recentRestrictions: 1,
      },
      costTrends: {
        trendDirection: "decreasing",
        growthRate: -5.2,
        seasonalPatterns: ["morning-peak"],
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalytics,
    } as Response);

    render(<CostManagementAdmin />);

    await waitFor(() => {
      expect(screen.getByText("Model Usage Analytics")).toBeInTheDocument(); // Correct heading text
      expect(screen.getByText("gpt-4")).toBeInTheDocument();
      const usageCountElements = screen.getAllByText("Usage Count:");
      expect(usageCountElements.length).toBeGreaterThan(0); // Check that at least one Usage Count label exists
      expect(screen.getByText("$300.00")).toBeInTheDocument();
    });
  });

  it("should show budget alerts", async () => {
    const mockAnalytics = {
      systemOverview: {
        totalSpend: 2000.0,
        totalUsers: 200,
        totalExecutions: 8000,
        averageCostPerUser: 10.0,
        period: "monthly",
      },
      topUsers: [],
      modelUsage: {},
      budgetAlerts: {
        activeAlerts: 15,
        criticalAlerts: 8,
        usersOverBudget: 12,
        recentRestrictions: 5,
      },
      costTrends: {
        trendDirection: "increasing",
        growthRate: 25.8,
        seasonalPatterns: ["weekend-surge"],
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalytics,
    } as Response);

    render(<CostManagementAdmin />);

    await waitFor(() => {
      expect(screen.getByText("Budget Alerts")).toBeInTheDocument();
      expect(screen.getByText("15")).toBeInTheDocument(); // activeAlerts
      expect(screen.getByText("8")).toBeInTheDocument(); // criticalAlerts
      expect(screen.getByText("12")).toBeInTheDocument(); // usersOverBudget
    });
  });

  it("should handle refresh functionality", async () => {
    const mockAnalytics = {
      systemOverview: {
        totalSpend: 1500.0,
        totalUsers: 150,
        totalExecutions: 6000,
        averageCostPerUser: 10.0,
        period: "monthly",
      },
      topUsers: [],
      modelUsage: {},
      budgetAlerts: {
        activeAlerts: 10,
        criticalAlerts: 3,
        usersOverBudget: 7,
        recentRestrictions: 2,
      },
      costTrends: {
        trendDirection: "stable",
        growthRate: 2.1,
        seasonalPatterns: [],
      },
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockAnalytics,
    } as Response);

    render(<CostManagementAdmin />);

    await waitFor(() => {
      expect(screen.getByText("$1500.00")).toBeInTheDocument(); // Remove comma
    });

    // Find and click refresh button
    const refreshButton = screen.getByRole("button", { name: /refresh/i });
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2); // Initial + refresh
    });
  });
});
