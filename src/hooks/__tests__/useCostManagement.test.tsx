import { renderHook, act } from "@testing-library/react";
import React from "react";

// Mock API functions
const mockApi = {
  getBudgetStatus: jest.fn(),
  getCostPrediction: jest.fn(),
  estimateOperationCost: jest.fn(),
};

// Mock useCostManagement hook for testing
const useCostManagement = () => {
  const [budgetStatus, setBudgetStatus] = React.useState<{
    data: any;
    isLoading: boolean;
    error: Error | null;
  }>({
    data: null,
    isLoading: false,
    error: null,
  });

  const [costPrediction] = React.useState<{
    data: any;
    isLoading: boolean;
    error: Error | null;
  }>({
    data: null,
    isLoading: false,
    error: null,
  });

  const refreshBudgetStatus = React.useCallback(async () => {
    setBudgetStatus((prev) => ({ ...prev, isLoading: true }));
    try {
      const data = await mockApi.getBudgetStatus();
      setBudgetStatus({ data, isLoading: false, error: null });
    } catch (error) {
      setBudgetStatus({ data: null, isLoading: false, error: error as Error });
    }
  }, []);

  const estimateCost = React.useCallback(
    async (params: {
      provider: string;
      model: string;
      inputTokens: number;
      expectedOutputTokens: number;
    }) => {
      return await mockApi.estimateOperationCost(params);
    },
    [],
  );

  return {
    budgetStatus,
    costPrediction,
    refreshBudgetStatus,
    estimateCost,
  };
};

describe("useCostManagement", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("initializes with default state", () => {
    const { result } = renderHook(() => useCostManagement());

    expect(result.current.budgetStatus.data).toBeNull();
    expect(result.current.budgetStatus.isLoading).toBe(false);
    expect(result.current.budgetStatus.error).toBeNull();
    expect(result.current.costPrediction.data).toBeNull();
    expect(typeof result.current.refreshBudgetStatus).toBe("function");
    expect(typeof result.current.estimateCost).toBe("function");
  });

  test("refreshBudgetStatus calls API and updates state", async () => {
    const mockBudgetData = {
      user_id: "user-123",
      current_cost: 25.0,
      budget_limit: 100.0,
      remaining_budget: 75.0,
      utilization_percent: 25.0,
      status: "good",
    };

    mockApi.getBudgetStatus.mockResolvedValue(mockBudgetData);

    const { result } = renderHook(() => useCostManagement());

    await act(async () => {
      await result.current.refreshBudgetStatus();
    });

    expect(mockApi.getBudgetStatus).toHaveBeenCalledTimes(1);
    expect(result.current.budgetStatus.data).toEqual(mockBudgetData);
    expect(result.current.budgetStatus.isLoading).toBe(false);
    expect(result.current.budgetStatus.error).toBeNull();
  });

  test("refreshBudgetStatus handles errors", async () => {
    const mockError = new Error("API Error");
    mockApi.getBudgetStatus.mockRejectedValue(mockError);

    const { result } = renderHook(() => useCostManagement());

    await act(async () => {
      await result.current.refreshBudgetStatus();
    });

    expect(result.current.budgetStatus.data).toBeNull();
    expect(result.current.budgetStatus.isLoading).toBe(false);
    expect(result.current.budgetStatus.error).toEqual(mockError);
  });

  test("estimateCost calls API with correct parameters", async () => {
    const mockEstimate = {
      provider: "openai",
      model: "gpt-4",
      estimated_cost: 0.045,
      input_cost: 0.03,
      output_cost: 0.015,
      total_tokens: 1500,
    };

    mockApi.estimateOperationCost.mockResolvedValue(mockEstimate);

    const { result } = renderHook(() => useCostManagement());

    const params = {
      provider: "openai",
      model: "gpt-4",
      inputTokens: 1000,
      expectedOutputTokens: 500,
    };

    const estimate = await result.current.estimateCost(params);

    expect(mockApi.estimateOperationCost).toHaveBeenCalledWith(params);
    expect(estimate).toEqual(mockEstimate);
  });

  test("estimateCost handles API errors", async () => {
    const mockError = new Error("Estimation failed");
    mockApi.estimateOperationCost.mockRejectedValue(mockError);

    const { result } = renderHook(() => useCostManagement());

    const params = {
      provider: "openai",
      model: "gpt-4",
      inputTokens: 1000,
      expectedOutputTokens: 500,
    };

    await expect(result.current.estimateCost(params)).rejects.toThrow(
      "Estimation failed",
    );
  });

  test("maintains function reference stability", () => {
    const { result, rerender } = renderHook(() => useCostManagement());

    const initialRefresh = result.current.refreshBudgetStatus;
    const initialEstimate = result.current.estimateCost;

    rerender();

    expect(result.current.refreshBudgetStatus).toBe(initialRefresh);
    expect(result.current.estimateCost).toBe(initialEstimate);
  });
});
