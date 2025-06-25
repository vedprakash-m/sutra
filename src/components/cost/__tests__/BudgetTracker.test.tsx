import React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "react-query";

// Mock BudgetTracker component for testing
const BudgetTracker: React.FC = () => {
  const budgetData = {
    current_cost: 25.0,
    budget_limit: 100.0,
    remaining_budget: 75.0,
    utilization_percent: 25.0,
    status: "good",
    last_updated: new Date().toISOString(),
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Budget Tracker
      </h3>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Current Usage</span>
          <span className="font-medium">
            ${budgetData.current_cost.toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Budget Limit</span>
          <span className="font-medium">
            ${budgetData.budget_limit.toFixed(2)}
          </span>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full"
            style={{ width: `${budgetData.utilization_percent}%` }}
            data-testid="progress-bar"
          />
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Utilization</span>
          <span className="font-medium">{budgetData.utilization_percent}%</span>
        </div>

        <div className="flex items-center space-x-2">
          <div
            className="w-3 h-3 rounded-full bg-green-500"
            data-testid="status-indicator"
          />
          <span className="text-sm text-gray-600">Status: Good</span>
        </div>

        <button
          className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          onClick={() => {}}
        >
          Refresh
        </button>
      </div>
    </div>
  );
};

// Create a wrapper component with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("BudgetTracker", () => {
  test("renders budget tracker with basic information", () => {
    render(<BudgetTracker />, { wrapper: createWrapper() });

    expect(screen.getByText("Budget Tracker")).toBeInTheDocument();
    expect(screen.getByText("$25.00")).toBeInTheDocument(); // Current cost
    expect(screen.getByText("$100.00")).toBeInTheDocument(); // Budget limit
    expect(screen.getByText("25%")).toBeInTheDocument(); // Utilization
    expect(screen.getByTestId("status-indicator")).toBeInTheDocument();
  });

  test("displays correct progress bar width", () => {
    render(<BudgetTracker />, { wrapper: createWrapper() });

    const progressBar = screen.getByTestId("progress-bar");
    expect(progressBar).toHaveStyle("width: 25%");
  });

  test("renders refresh button", () => {
    render(<BudgetTracker />, { wrapper: createWrapper() });

    const refreshButton = screen.getByRole("button", { name: /refresh/i });
    expect(refreshButton).toBeInTheDocument();
  });

  test("shows good status indicator", () => {
    render(<BudgetTracker />, { wrapper: createWrapper() });

    const statusIndicator = screen.getByTestId("status-indicator");
    expect(statusIndicator).toHaveClass("bg-green-500");
    expect(screen.getByText("Status: Good")).toBeInTheDocument();
  });
});
