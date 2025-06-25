import React from "react";
import useCostManagement from "../../hooks/useCostManagement";

interface BudgetTrackerProps {
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

const BudgetTracker: React.FC<BudgetTrackerProps> = ({
  className = "",
  showDetails = true,
  compact = false,
}) => {
  const {
    budgetStatus,
    loading,
    error,
    getBudgetColor,
    formatCurrency,
    isOverBudget,
    isCritical,
    hasRestrictions,
  } = useCostManagement();

  if (loading && !budgetStatus) {
    return (
      <div className={`budget-tracker animate-pulse ${className}`}>
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-2 bg-gray-200 rounded w-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`budget-tracker text-red-600 text-sm ${className}`}>
        ⚠️ {error}
      </div>
    );
  }

  if (!budgetStatus) {
    return (
      <div className={`budget-tracker text-gray-500 text-sm ${className}`}>
        No budget configured
      </div>
    );
  }

  const utilizationPercent = Math.min(budgetStatus.utilization * 100, 100);
  const progressColor = getBudgetColor(utilizationPercent);

  if (compact) {
    return (
      <div
        className={`budget-tracker-compact flex items-center space-x-2 ${className}`}
      >
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-300"
            style={{
              width: `${utilizationPercent}%`,
              backgroundColor: progressColor,
            }}
          />
        </div>
        <span className="text-sm font-medium whitespace-nowrap">
          {formatCurrency(budgetStatus.currentSpend)} /{" "}
          {formatCurrency(budgetStatus.budgetAmount)}
        </span>
        {hasRestrictions && <span className="text-orange-500 text-sm">🚫</span>}
      </div>
    );
  }

  return (
    <div
      className={`budget-tracker bg-white rounded-lg border shadow-sm p-4 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">Budget Usage</h3>
        <div className="flex items-center space-x-2">
          {isOverBudget && (
            <span className="text-red-600 text-sm font-medium">
              Over Budget
            </span>
          )}
          {isCritical && !isOverBudget && (
            <span className="text-orange-600 text-sm font-medium">
              Critical
            </span>
          )}
          {hasRestrictions && (
            <span className="text-orange-600 text-sm">Restrictions Active</span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>
            {formatCurrency(budgetStatus.currentSpend)} /{" "}
            {formatCurrency(budgetStatus.budgetAmount)}
          </span>
          <span>{utilizationPercent.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="h-3 rounded-full transition-all duration-300 flex items-center justify-end pr-1"
            style={{
              width: `${utilizationPercent}%`,
              backgroundColor: progressColor,
            }}
          >
            {utilizationPercent > 10 && (
              <div className="w-1.5 h-1.5 bg-white rounded-full opacity-80"></div>
            )}
          </div>
        </div>
      </div>

      {/* Budget Details */}
      {showDetails && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Remaining Budget:</span>
            <span
              className={
                budgetStatus.remainingBudget < 0
                  ? "text-red-600 font-medium"
                  : "text-gray-900"
              }
            >
              {formatCurrency(Math.max(0, budgetStatus.remainingBudget))}
            </span>
          </div>

          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Executions:</span>
            <span className="text-gray-900">{budgetStatus.executionCount}</span>
          </div>

          {budgetStatus.timeRemaining && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Period Remaining:</span>
              <span className="text-gray-900">
                {budgetStatus.timeRemaining}
              </span>
            </div>
          )}

          {/* Active Restrictions */}
          {hasRestrictions && (
            <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded">
              <p className="text-sm text-orange-800 font-medium mb-1">
                Active Restrictions:
              </p>
              <ul className="text-sm text-orange-700">
                {budgetStatus.restrictionsActive.map(
                  (restriction: string, index: number) => (
                    <li key={index} className="flex items-center">
                      <span className="w-1 h-1 bg-orange-500 rounded-full mr-2"></span>
                      {restriction}
                    </li>
                  ),
                )}
              </ul>
            </div>
          )}

          {/* Model Usage Breakdown */}
          {Object.keys(budgetStatus.modelUsage || {}).length > 0 && (
            <div className="mt-3">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Model Usage:
              </p>
              <div className="space-y-1">
                {Object.entries(budgetStatus.modelUsage).map(
                  ([model, usage]: [string, any]) => (
                    <div key={model} className="flex justify-between text-sm">
                      <span className="text-gray-600">{model}:</span>
                      <div className="text-right">
                        <span className="text-gray-900">
                          {formatCurrency(usage.cost)}
                        </span>
                        <span className="text-gray-500 ml-1">
                          ({usage.calls} calls)
                        </span>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Alert Messages */}
      {budgetStatus.alertLevel === "exceeded" && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-800">
            ⚠️ Budget exceeded. Some features may be restricted until the next
            billing period.
          </p>
        </div>
      )}

      {budgetStatus.alertLevel === "critical" && (
        <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded">
          <p className="text-sm text-orange-800">
            ⚠️ Budget critically low. Consider optimizing your usage or
            increasing your budget.
          </p>
        </div>
      )}
    </div>
  );
};

export default BudgetTracker;
