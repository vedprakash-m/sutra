import { useState, useEffect, useCallback } from "react";

// TODO: Import actual auth hook when available
// import { useAuth } from './useAuth';

// Temporary mock for auth hook
const useAuth = () => ({
  user: { id: "current-user-id" },
  apiCall: async (url: string, options?: any) => {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer token", // TODO: Get actual token
        ...options?.headers,
      },
    });
    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }
    return response.json();
  },
});

export interface BudgetStatus {
  currentSpend: number;
  budgetAmount: number;
  utilization: number;
  alertLevel: "safe" | "warning" | "critical" | "exceeded";
  restrictionsActive: string[];
  timeRemaining: string;
  executionCount: number;
  modelUsage: Record<string, { calls: number; cost: number; tokens: number }>;
  remainingBudget: number;
}

export interface CostEstimate {
  model: string;
  estimatedCost: number;
  breakdown: {
    inputCost: number;
    outputCost: number;
    estimatedInputTokens: number;
    estimatedOutputTokens: number;
  };
  cheaperAlternatives: Array<{
    model: string;
    estimatedCost: number;
    savingsPercent: number;
    qualityImpact: string;
  }>;
  budgetCheck: {
    allowed: boolean;
    reason?: string;
    warning?: string;
    utilization?: number;
    alternatives?: any[];
  };
}

export interface CostPrediction {
  predictedSpend: number;
  confidenceInterval: {
    lower: number;
    upper: number;
  };
  recommendations: string[];
  trendDirection: "increasing" | "stable" | "decreasing";
  riskLevel: "low" | "medium" | "high";
}

export interface AccessRestrictions {
  allowed: boolean;
  reason?: string;
  message?: string;
  fallbackModel?: string;
}

export const useCostManagement = () => {
  const { user, apiCall } = useAuth();
  const [budgetStatus, setBudgetStatus] = useState<BudgetStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Real-time budget monitoring
  useEffect(() => {
    if (!user) return;

    const fetchBudgetStatus = async () => {
      try {
        const response = await apiCall(`/api/cost/budget/usage/${user.id}`);
        setBudgetStatus(response);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch budget status:", err);
        setError("Failed to load budget information");
      }
    };

    // Initial fetch
    fetchBudgetStatus();

    // Set up real-time updates every 30 seconds
    const interval = setInterval(fetchBudgetStatus, 30000);

    return () => clearInterval(interval);
  }, [user, apiCall]);

  const createBudgetConfig = useCallback(
    async (configData: {
      entityType: string;
      entityId: string;
      budgetAmount: number;
      budgetPeriod: string;
      alertThresholds?: number[];
      autoActions?: Record<string, string[]>;
      modelRestrictions?: Record<string, any>;
    }) => {
      setLoading(true);
      try {
        const response = await apiCall("/api/cost/budget/config", {
          method: "POST",
          body: JSON.stringify(configData),
        });
        setError(null);
        return response;
      } catch (err) {
        setError("Failed to create budget configuration");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiCall],
  );

  const estimateExecutionCost = useCallback(
    async (
      model: string,
      prompt: string,
      maxTokens: number = 1000,
    ): Promise<CostEstimate> => {
      try {
        const response = await apiCall("/api/cost/estimate", {
          method: "POST",
          body: JSON.stringify({
            model,
            prompt,
            max_tokens: maxTokens,
          }),
        });
        return response;
      } catch (err) {
        console.error("Failed to estimate cost:", err);
        throw new Error("Failed to estimate execution cost");
      }
    },
    [apiCall],
  );

  const getCostPredictions = useCallback(
    async (entityId?: string): Promise<CostPrediction> => {
      try {
        const targetId = entityId || user?.id;
        const response = await apiCall(
          `/api/cost/budget/predictions/${targetId}`,
        );
        return response;
      } catch (err) {
        console.error("Failed to get cost predictions:", err);
        throw new Error("Failed to get cost predictions");
      }
    },
    [apiCall, user],
  );

  const checkAccessRestrictions = useCallback(
    async (entityId?: string, model?: string): Promise<AccessRestrictions> => {
      try {
        const targetId = entityId || user?.id;
        const url = model
          ? `/api/cost/restrictions/${targetId}?model=${model}`
          : `/api/cost/restrictions/${targetId}`;

        const response = await apiCall(url);
        return response;
      } catch (err) {
        console.error("Failed to check access restrictions:", err);
        return { allowed: true }; // Allow on error to avoid blocking users
      }
    },
    [apiCall, user],
  );

  const getBudgetColor = useCallback((utilization: number): string => {
    if (utilization >= 100) return "#ef4444"; // red-500
    if (utilization >= 90) return "#f97316"; // orange-500
    if (utilization >= 75) return "#eab308"; // yellow-500
    return "#22c55e"; // green-500
  }, []);

  const getAlertLevel = useCallback(
    (utilization: number): BudgetStatus["alertLevel"] => {
      if (utilization >= 100) return "exceeded";
      if (utilization >= 90) return "critical";
      if (utilization >= 75) return "warning";
      return "safe";
    },
    [],
  );

  const formatCurrency = useCallback(
    (amount: number, currency: string = "USD"): string => {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 4,
      }).format(amount);
    },
    [],
  );

  const shouldShowCostWarning = useCallback(
    (estimate: CostEstimate): boolean => {
      return (
        estimate.budgetCheck.allowed === false ||
        estimate.budgetCheck.warning !== undefined ||
        (estimate.budgetCheck.utilization !== undefined &&
          estimate.budgetCheck.utilization > 75)
      );
    },
    [],
  );

  const getRecommendedModel = useCallback(
    (estimate: CostEstimate): string | null => {
      if (
        estimate.budgetCheck.alternatives &&
        estimate.budgetCheck.alternatives.length > 0
      ) {
        return estimate.budgetCheck.alternatives[0].model;
      }
      if (
        estimate.cheaperAlternatives &&
        estimate.cheaperAlternatives.length > 0
      ) {
        const bestAlternative = estimate.cheaperAlternatives.find(
          (alt) =>
            alt.qualityImpact === "minimal" || alt.qualityImpact === "none",
        );
        return bestAlternative?.model || estimate.cheaperAlternatives[0].model;
      }
      return null;
    },
    [],
  );

  return {
    // State
    budgetStatus,
    loading,
    error,

    // Actions
    createBudgetConfig,
    estimateExecutionCost,
    getCostPredictions,
    checkAccessRestrictions,

    // Utilities
    getBudgetColor,
    getAlertLevel,
    formatCurrency,
    shouldShowCostWarning,
    getRecommendedModel,

    // Computed values
    isOverBudget: budgetStatus ? budgetStatus.utilization >= 100 : false,
    isCritical: budgetStatus ? budgetStatus.utilization >= 90 : false,
    hasRestrictions: budgetStatus
      ? (budgetStatus.restrictionsActive?.length || 0) > 0
      : false,
  };
};

export default useCostManagement;
