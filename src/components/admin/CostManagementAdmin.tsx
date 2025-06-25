import React, { useState, useEffect } from "react";
import useCostManagement from "../../hooks/useCostManagement";

interface CostAnalytics {
  systemOverview: {
    totalSpend: number;
    totalUsers: number;
    totalExecutions: number;
    averageCostPerUser: number;
    period: string;
  };
  topUsers: Array<{
    userId: string;
    cost: number;
    executions: number;
  }>;
  modelUsage: Record<
    string,
    {
      usageCount: number;
      totalCost: number;
      avgCost: number;
    }
  >;
  budgetAlerts: {
    activeAlerts: number;
    criticalAlerts: number;
    usersOverBudget: number;
    recentRestrictions: number;
  };
  costTrends: {
    trendDirection: string;
    growthRate: number;
    seasonalPatterns: string[];
  };
}

const CostManagementAdmin: React.FC = () => {
  const { formatCurrency } = useCostManagement();
  const [analytics, setAnalytics] = useState<CostAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timePeriod, setTimePeriod] = useState("monthly");

  useEffect(() => {
    fetchAnalytics();
  }, [timePeriod]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/cost/analytics?period=${timePeriod}`, {
        headers: {
          Authorization: "Bearer token", // TODO: Get actual token
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch analytics");
      }

      const data = await response.json();
      setAnalytics(data);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch cost analytics:", err);
      setError("Failed to load cost analytics");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-red-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return <div>No analytics data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Cost Management</h2>
        <div className="flex items-center space-x-4">
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 bg-white text-sm"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
          </select>
          <button
            onClick={fetchAnalytics}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">💰</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Spend
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatCurrency(analytics.systemOverview.totalSpend)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">👥</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Users
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.systemOverview.totalUsers}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">⚡</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Executions
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.systemOverview.totalExecutions.toLocaleString()}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">📊</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Avg Cost/User
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatCurrency(
                      analytics.systemOverview.averageCostPerUser,
                    )}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      {analytics.budgetAlerts && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Budget Alerts
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {analytics.budgetAlerts.activeAlerts}
                </div>
                <div className="text-sm text-gray-500">Active Alerts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {analytics.budgetAlerts.criticalAlerts}
                </div>
                <div className="text-sm text-gray-500">Critical Alerts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {analytics.budgetAlerts.usersOverBudget}
                </div>
                <div className="text-sm text-gray-500">Users Over Budget</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {analytics.budgetAlerts.recentRestrictions}
                </div>
                <div className="text-sm text-gray-500">Recent Restrictions</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Users Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Top Users by Cost
          </h3>
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Executions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Cost/Execution
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.topUsers.map((user, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {user.userId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(user.cost)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.executions}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(user.cost / user.executions)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Model Usage Analytics */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Model Usage Analytics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(analytics.modelUsage).map(([model, usage]) => (
              <div
                key={model}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="font-medium text-gray-900 mb-2">{model}</div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Usage Count:</span>
                    <span className="text-gray-900">{usage.usageCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Total Cost:</span>
                    <span className="text-gray-900">
                      {formatCurrency(usage.totalCost)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Avg Cost:</span>
                    <span className="text-gray-900">
                      {formatCurrency(usage.avgCost)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Cost Trends */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Cost Trends
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div
                className={`text-2xl font-bold ${
                  analytics.costTrends.trendDirection === "increasing"
                    ? "text-red-600"
                    : analytics.costTrends.trendDirection === "decreasing"
                      ? "text-green-600"
                      : "text-gray-600"
                }`}
              >
                {analytics.costTrends.trendDirection === "increasing"
                  ? "📈"
                  : analytics.costTrends.trendDirection === "decreasing"
                    ? "📉"
                    : "➡️"}
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {analytics.costTrends.trendDirection}
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {analytics.costTrends.growthRate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-500 mt-1">Growth Rate</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">
                <div className="font-medium mb-1">Patterns:</div>
                {analytics.costTrends.seasonalPatterns.map((pattern, index) => (
                  <div key={index} className="text-xs text-gray-500">
                    {pattern
                      .replace("_", " ")
                      .replace(/\b\w/g, (l) => l.toUpperCase())}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostManagementAdmin;
