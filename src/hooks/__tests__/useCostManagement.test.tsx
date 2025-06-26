import { renderHook, act } from "@testing-library/react";
import useCostManagement from "../useCostManagement";

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("useCostManagement - Simple Tests", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    jest.clearAllMocks();
  });

  it("should initialize with default values", () => {
    // Mock initial budget status call to return null/error
    mockFetch.mockRejectedValueOnce(new Error("No budget"));

    const { result } = renderHook(() => useCostManagement());

    expect(result.current.budgetStatus).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isOverBudget).toBe(false);
    expect(result.current.isCritical).toBe(false);
    expect(result.current.hasRestrictions).toBe(false);
  });

  it("should have basic functionality available", () => {
    mockFetch.mockRejectedValueOnce(new Error("No budget"));

    const { result } = renderHook(() => useCostManagement());

    expect(typeof result.current.createBudgetConfig).toBe("function");
    expect(typeof result.current.estimateExecutionCost).toBe("function");
    expect(typeof result.current.getCostPredictions).toBe("function");
    expect(typeof result.current.checkAccessRestrictions).toBe("function");
    expect(typeof result.current.getBudgetColor).toBe("function");
    expect(typeof result.current.getAlertLevel).toBe("function");
    expect(typeof result.current.formatCurrency).toBe("function");
    expect(typeof result.current.shouldShowCostWarning).toBe("function");
    expect(typeof result.current.getRecommendedModel).toBe("function");
  });

  it("should return formatted currency correctly", () => {
    mockFetch.mockRejectedValueOnce(new Error("No budget"));

    const { result } = renderHook(() => useCostManagement());

    expect(result.current.formatCurrency(1.23)).toBe("$1.23");
    expect(result.current.formatCurrency(0.001)).toBe("$0.001");
  });

  it("should detect cost warnings correctly", () => {
    mockFetch.mockRejectedValueOnce(new Error("No budget"));

    const { result } = renderHook(() => useCostManagement());

    const lowCostEstimate = {
      model: "gpt-3.5-turbo",
      estimatedCost: 10,
      breakdown: {
        inputCost: 5,
        outputCost: 5,
        estimatedInputTokens: 100,
        estimatedOutputTokens: 100,
      },
      cheaperAlternatives: [],
      budgetCheck: { allowed: true },
    };

    const highCostEstimate = {
      model: "gpt-4",
      estimatedCost: 60,
      breakdown: {
        inputCost: 30,
        outputCost: 30,
        estimatedInputTokens: 100,
        estimatedOutputTokens: 100,
      },
      cheaperAlternatives: [],
      budgetCheck: { allowed: true },
    };

    expect(result.current.shouldShowCostWarning(lowCostEstimate)).toBe(false);
    expect(result.current.shouldShowCostWarning(highCostEstimate)).toBe(false);
  });

  it("should get alert level correctly", () => {
    mockFetch.mockRejectedValueOnce(new Error("No budget"));

    const { result } = renderHook(() => useCostManagement());

    expect(result.current.getAlertLevel(30)).toBe("safe");
    expect(result.current.getAlertLevel(75)).toBe("warning");
    expect(result.current.getAlertLevel(95)).toBe("critical");
  });

  it("should get budget color correctly", () => {
    mockFetch.mockRejectedValueOnce(new Error("No budget"));

    const { result } = renderHook(() => useCostManagement());

    expect(result.current.getBudgetColor(30)).toBe("#22c55e");
    expect(result.current.getBudgetColor(75)).toBe("#eab308");
    expect(result.current.getBudgetColor(95)).toBe("#f97316");
  });

  it("should get recommended model for null alternatives", () => {
    mockFetch.mockRejectedValueOnce(new Error("No budget"));

    const { result } = renderHook(() => useCostManagement());

    const estimateWithNoAlternatives = {
      model: "gpt-4",
      estimatedCost: 0.05,
      breakdown: {
        inputCost: 0.03,
        outputCost: 0.02,
        estimatedInputTokens: 100,
        estimatedOutputTokens: 100,
      },
      cheaperAlternatives: [],
      budgetCheck: { allowed: true },
    };

    expect(
      result.current.getRecommendedModel(estimateWithNoAlternatives),
    ).toBeNull();
  });

  it("should handle async functions without throwing", async () => {
    // Setup proper mocks for async calls
    mockFetch
      .mockRejectedValueOnce(new Error("Budget failed")) // Initial budget call
      .mockResolvedValueOnce({
        // Create budget config
        ok: true,
        json: async () => ({ success: true }),
      })
      .mockResolvedValueOnce({
        // Estimate cost
        ok: true,
        json: async () => ({
          model: "gpt-3.5-turbo",
          estimatedCost: 0.01,
          breakdown: {
            inputCost: 0.005,
            outputCost: 0.005,
            estimatedInputTokens: 50,
            estimatedOutputTokens: 50,
          },
          cheaperAlternatives: [],
          budgetCheck: { allowed: true },
        }),
      })
      .mockResolvedValueOnce({
        // Get predictions
        ok: true,
        json: async () => ({
          predictedSpend: 50,
          confidenceInterval: { lower: 40, upper: 60 },
          recommendations: [],
          trendDirection: "stable",
          riskLevel: "low",
        }),
      })
      .mockResolvedValueOnce({
        // Check restrictions
        ok: true,
        json: async () => ({ allowed: true }),
      });

    const { result } = renderHook(() => useCostManagement());

    // Test all async functions
    await act(async () => {
      const config = await result.current.createBudgetConfig({
        entityType: "user",
        entityId: "test-user",
        budgetAmount: 100,
        budgetPeriod: "monthly",
        alertThresholds: [70, 90],
      });
      expect(config).toEqual({ success: true });
    });

    await act(async () => {
      const estimate = await result.current.estimateExecutionCost(
        "gpt-3.5-turbo",
        "test prompt",
      );
      expect(estimate.model).toBe("gpt-3.5-turbo");
    });

    await act(async () => {
      const prediction = await result.current.getCostPredictions();
      expect(prediction.predictedSpend).toBe(50);
    });

    await act(async () => {
      const restrictions = await result.current.checkAccessRestrictions();
      expect(restrictions.allowed).toBe(true);
    });
  });
});
