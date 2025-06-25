import React, { useEffect, useState } from "react";
import useCostManagement from "../../hooks/useCostManagement";

interface CostPreviewProps {
  prompt: string;
  model: string;
  maxTokens?: number;
  onModelChange?: (model: string) => void;
  className?: string;
}

const CostPreview: React.FC<CostPreviewProps> = ({
  prompt,
  model,
  maxTokens = 1000,
  onModelChange,
  className = "",
}) => {
  const {
    estimateExecutionCost,
    formatCurrency,
    shouldShowCostWarning,
    getRecommendedModel,
  } = useCostManagement();

  const [estimate, setEstimate] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!prompt || !model) return;

    const estimateCost = async () => {
      if (prompt.length < 10) return; // Don't estimate for very short prompts

      setLoading(true);
      setError(null);

      try {
        const result = await estimateExecutionCost(model, prompt, maxTokens);
        setEstimate(result);
      } catch (err) {
        console.error("Cost estimation failed:", err);
        setError("Failed to estimate cost");
      } finally {
        setLoading(false);
      }
    };

    // Debounce the estimation
    const timeoutId = setTimeout(estimateCost, 500);
    return () => clearTimeout(timeoutId);
  }, [prompt, model, maxTokens, estimateExecutionCost]);

  if (!prompt || prompt.length < 10) {
    return null;
  }

  if (loading) {
    return (
      <div
        className={`cost-preview animate-pulse bg-gray-50 rounded-lg p-3 ${className}`}
      >
        <div className="flex items-center space-x-2">
          <div className="h-4 bg-gray-200 rounded w-24"></div>
          <div className="h-4 bg-gray-200 rounded w-16"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`cost-preview bg-red-50 border border-red-200 rounded-lg p-3 ${className}`}
      >
        <p className="text-sm text-red-600">⚠️ {error}</p>
      </div>
    );
  }

  if (!estimate) {
    return null;
  }

  const showWarning = shouldShowCostWarning(estimate);
  const recommendedModel = getRecommendedModel(estimate);

  return (
    <div className={`cost-preview ${className}`}>
      {/* Main Cost Display */}
      <div
        className={`rounded-lg p-3 border ${
          showWarning
            ? "bg-yellow-50 border-yellow-200"
            : "bg-gray-50 border-gray-200"
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Estimated cost:</span>
            <span className="font-semibold text-gray-900">
              {formatCurrency(estimate.estimatedCost)}
            </span>
          </div>

          {estimate.breakdown && (
            <div className="text-xs text-gray-500">
              {estimate.breakdown.estimatedInputTokens +
                estimate.breakdown.estimatedOutputTokens}{" "}
              tokens
            </div>
          )}
        </div>

        {/* Budget Warning */}
        {showWarning && (
          <div className="mt-2">
            {estimate.budgetCheck.allowed === false && (
              <div className="flex items-center text-sm text-red-600">
                <span className="mr-1">🚫</span>
                <span>Execution blocked: {estimate.budgetCheck.reason}</span>
              </div>
            )}

            {estimate.budgetCheck.warning && (
              <div className="flex items-center text-sm text-yellow-700">
                <span className="mr-1">⚠️</span>
                <span>
                  Budget{" "}
                  {estimate.budgetCheck.warning === "budget_critical"
                    ? "critically low"
                    : "warning"}
                  {estimate.budgetCheck.utilization &&
                    ` (${estimate.budgetCheck.utilization.toFixed(1)}% used)`}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Cost Breakdown */}
        {estimate.breakdown && (
          <div className="mt-2 text-xs text-gray-600">
            Input: {formatCurrency(estimate.breakdown.inputCost)} • Output:{" "}
            {formatCurrency(estimate.breakdown.outputCost)}
          </div>
        )}
      </div>

      {/* Cheaper Alternatives */}
      {(estimate.cheaperAlternatives?.length > 0 || recommendedModel) && (
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm font-medium text-blue-800 mb-2">
            💡 Cost Optimization
          </p>

          {recommendedModel && onModelChange && (
            <div className="mb-2">
              <button
                onClick={() => onModelChange(recommendedModel)}
                className="text-sm text-blue-700 hover:text-blue-800 underline"
              >
                Switch to {recommendedModel} for better budget efficiency
              </button>
            </div>
          )}

          {estimate.cheaperAlternatives?.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-blue-700 mb-1">
                Cheaper alternatives:
              </p>
              {estimate.cheaperAlternatives
                .slice(0, 2)
                .map((alt: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="text-blue-700">
                      {alt.model}
                      {onModelChange && (
                        <button
                          onClick={() => onModelChange(alt.model)}
                          className="ml-1 text-blue-600 hover:text-blue-800 underline"
                        >
                          (switch)
                        </button>
                      )}
                    </span>
                    <div className="text-blue-600">
                      <span>{formatCurrency(alt.estimatedCost)}</span>
                      <span className="ml-1 text-green-600">
                        (-{alt.savingsPercent}%)
                      </span>
                    </div>
                  </div>
                ))}

              {estimate.cheaperAlternatives.some(
                (alt: any) =>
                  alt.qualityImpact &&
                  alt.qualityImpact !== "none" &&
                  alt.qualityImpact !== "minimal",
              ) && (
                <p className="text-xs text-blue-600 mt-1">
                  ⓘ Quality may vary with cheaper models
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Budget Impact */}
      {estimate.budgetCheck?.utilization !== undefined && (
        <div className="mt-2 text-xs text-gray-600">
          Budget impact: +
          {(
            (estimate.estimatedCost /
              (estimate.budgetCheck.utilization / 100)) *
            100
          ).toFixed(1)}
          % utilization
        </div>
      )}
    </div>
  );
};

export default CostPreview;
