import React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "react-query";
import BudgetTracker from "../BudgetTracker";

// Mock the useCostManagement hook
jest.mock("../../../hooks/useCostManagement", () => ({
  __esModule: true,
  default: jest.fn(),
}));

const mockUseCostManagement =
  require("../../../hooks/useCostManagement").default;

describe("BudgetTracker", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>,
    );
  };

  it("should render loading state", () => {
    mockUseCostManagement.mockReturnValue({
      budgetStatus: null,
      loading: true,
      error: null,
      getBudgetColor: jest.fn(),
      formatCurrency: jest.fn(),
      isOverBudget: false,
      isCritical: false,
      hasRestrictions: false,
    });

    renderWithQueryClient(<BudgetTracker />);
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("should render error state", () => {
    mockUseCostManagement.mockReturnValue({
      budgetStatus: null,
      loading: false,
      error: "Failed to load budget",
      getBudgetColor: jest.fn(),
      formatCurrency: jest.fn(),
      isOverBudget: false,
      isCritical: false,
      hasRestrictions: false,
    });

    renderWithQueryClient(<BudgetTracker />);
    expect(screen.getByText("⚠️ Failed to load budget")).toBeInTheDocument();
  });

  it("should render no budget configured", () => {
    mockUseCostManagement.mockReturnValue({
      budgetStatus: null,
      loading: false,
      error: null,
      getBudgetColor: jest.fn(),
      formatCurrency: jest.fn(),
      isOverBudget: false,
      isCritical: false,
      hasRestrictions: false,
    });

    renderWithQueryClient(<BudgetTracker />);
    expect(screen.getByText("No budget configured")).toBeInTheDocument();
  });

  it("should render budget status with details", () => {
    const mockBudgetStatus = {
      currentSpend: 25.0,
      budgetAmount: 100.0,
      remainingBudget: 75.0,
      utilization: 0.25,
      alertLevel: "safe" as const,
      restrictionsActive: [],
      timeRemaining: "15 days",
      executionCount: 150,
      modelUsage: {},
    };

    mockUseCostManagement.mockReturnValue({
      budgetStatus: mockBudgetStatus,
      loading: false,
      error: null,
      getBudgetColor: jest.fn().mockReturnValue("#22c55e"),
      formatCurrency: jest
        .fn()
        .mockImplementation((val) => `$${val.toFixed(2)}`),
      isOverBudget: false,
      isCritical: false,
      hasRestrictions: false,
    });

    renderWithQueryClient(<BudgetTracker showDetails={true} />);
    expect(screen.getByText("Budget Usage")).toBeInTheDocument();
    expect(screen.getByText("$25.00 / $100.00")).toBeInTheDocument();
    expect(screen.getByText("25.0%")).toBeInTheDocument();
  });

  it("should render compact view", () => {
    const mockBudgetStatus = {
      currentSpend: 25.0,
      budgetAmount: 100.0,
      remainingBudget: 75.0,
      utilization: 0.25,
      alertLevel: "safe" as const,
      restrictionsActive: [],
      timeRemaining: "15 days",
      executionCount: 150,
      modelUsage: {},
    };

    mockUseCostManagement.mockReturnValue({
      budgetStatus: mockBudgetStatus,
      loading: false,
      error: null,
      getBudgetColor: jest.fn().mockReturnValue("#22c55e"),
      formatCurrency: jest
        .fn()
        .mockImplementation((val) => `$${val.toFixed(2)}`),
      isOverBudget: false,
      isCritical: false,
      hasRestrictions: false,
    });

    renderWithQueryClient(<BudgetTracker compact={true} />);
    expect(screen.getByText("$25.00 / $100.00")).toBeInTheDocument();
  });

  it("should handle over budget status", () => {
    const mockBudgetStatus = {
      currentSpend: 120.0,
      budgetAmount: 100.0,
      remainingBudget: -20.0,
      utilization: 1.2,
      alertLevel: "exceeded" as const,
      restrictionsActive: ["model-restriction"],
      timeRemaining: "5 days",
      executionCount: 300,
      modelUsage: {},
    };

    mockUseCostManagement.mockReturnValue({
      budgetStatus: mockBudgetStatus,
      loading: false,
      error: null,
      getBudgetColor: jest.fn().mockReturnValue("#ef4444"),
      formatCurrency: jest
        .fn()
        .mockImplementation((val) => `$${val.toFixed(2)}`),
      isOverBudget: true,
      isCritical: true,
      hasRestrictions: true,
    });

    renderWithQueryClient(<BudgetTracker />);
    expect(screen.getByText("Over Budget")).toBeInTheDocument();
    expect(screen.getByText("Restrictions Active")).toBeInTheDocument();
  });

  it("should render refresh functionality", () => {
    const mockBudgetStatus = {
      currentSpend: 25.0,
      budgetAmount: 100.0,
      remainingBudget: 75.0,
      utilization: 0.25,
      alertLevel: "safe" as const,
      restrictionsActive: [],
      timeRemaining: "15 days",
      executionCount: 150,
      modelUsage: {},
    };

    mockUseCostManagement.mockReturnValue({
      budgetStatus: mockBudgetStatus,
      loading: false,
      error: null,
      getBudgetColor: jest.fn().mockReturnValue("#22c55e"),
      formatCurrency: jest
        .fn()
        .mockImplementation((val) => `$${val.toFixed(2)}`),
      isOverBudget: false,
      isCritical: false,
      hasRestrictions: false,
    });

    renderWithQueryClient(<BudgetTracker />);
    expect(screen.getByText("Budget Usage")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument(); // execution count
  });
});
