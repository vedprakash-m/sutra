import { useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useApi } from "@/hooks/useApi";
import { adminApi } from "@/services/api";
import CostManagementAdmin from "./CostManagementAdmin";

export default function AdminPanel() {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState<
    "overview" | "llm" | "users" | "system" | "cost"
  >("overview");

  // Fetch admin data
  const { data: systemHealth, loading: healthLoading } = useApi(
    () => adminApi.getSystemHealth(),
    [],
  );
  const { data: usageStats, loading: usageLoading } = useApi(
    () => adminApi.getUsageStats(),
    [],
  );
  const { data: llmSettings, loading: llmLoading } = useApi(
    () => adminApi.getLLMSettings(),
    [],
  );

  // Cast to any for MVP to avoid type issues
  const health = systemHealth as any;
  const usage = usageStats as any;
  const llm = llmSettings as any;

  // Handler for LLM configuration
  const handleLLMConfiguration = (provider: string) => {
    const currentConfig = llm?.[provider];
    const apiKey = prompt(
      `Configure ${provider} API Settings:\n\n` + "Enter your API key:",
      currentConfig?.apiKey ? "***************************" : "",
    );

    if (apiKey && apiKey !== "***************************") {
      // In a real implementation, this would call the backend API
      console.log(`🔧 Configuring ${provider} with new API key`);
      alert(
        `${provider} configuration updated! (Note: This is a demo - actual API integration would save to backend)`,
      );
    }
  };

  if (!isAdmin) {
    return (
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
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
              <h3 className="text-sm font-medium text-red-800">
                Access Denied
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>
                  You do not have administrative privileges to access this page.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage system settings, users, and LLM configurations
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "overview", name: "Overview" },
            { id: "llm", name: "LLM Settings" },
            { id: "cost", name: "Cost Management" },
            { id: "users", name: "User Management" },
            { id: "system", name: "System Health" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-4">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-1a1.5 1.5 0 01-3 0V5.499c0-1.376-1.05-2.532-2.386-2.545M15 8.25a4.5 4.5 0 11-6.168-4.168A4.502 4.502 0 0115 8.25zM15 8.25L18 12"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Users
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {usageLoading ? "..." : usage?.total_users || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Monthly Usage
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    $
                    {usageLoading
                      ? "..."
                      : (usage?.monthly_cost || 0).toFixed(2)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Prompts
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {usageLoading ? "..." : usage?.total_prompts || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    API Status
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {healthLoading ? "..." : health?.api_status || "Unknown"}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LLM Settings Tab */}
      {activeTab === "llm" && (
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              LLM Provider Configuration
            </h2>
            {llmLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading LLM settings...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {["openai", "anthropic", "google"].map((provider) => (
                  <div
                    key={provider}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-indigo-500 rounded-lg flex items-center justify-center">
                          <span className="text-white text-sm font-medium capitalize">
                            {provider.charAt(0)}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-sm font-medium text-gray-900 capitalize">
                          {provider}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {llm?.[provider]?.enabled
                            ? "Configured and enabled"
                            : "Not configured"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          llm?.[provider]?.enabled
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {llm?.[provider]?.enabled ? "Active" : "Inactive"}
                      </span>
                      <button
                        onClick={() => handleLLMConfiguration(provider)}
                        className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700"
                      >
                        Configure
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* System Health Tab */}
      {activeTab === "system" && (
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              System Status
            </h2>
            {healthLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Checking system health...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    API Service
                  </span>
                  <span
                    className={`text-sm ${health?.api_status === "healthy" ? "text-green-600" : "text-red-600"}`}
                  >
                    {health?.api_status || "Unknown"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Database
                  </span>
                  <span
                    className={`text-sm ${health?.database_status === "connected" ? "text-green-600" : "text-red-600"}`}
                  >
                    {health?.database_status || "Unknown"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Storage
                  </span>
                  <span
                    className={`text-sm ${health?.storage_status === "available" ? "text-green-600" : "text-red-600"}`}
                  >
                    {health?.storage_status || "Unknown"}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Cost Management Tab */}
      {activeTab === "cost" && <CostManagementAdmin />}

      {/* User Management Tab */}
      {activeTab === "users" && (
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              User Management
            </h2>
            <div className="text-center py-4">
              <p className="text-gray-600 mb-4">
                Full user management interface is available at:
              </p>
              <a
                href="/admin.html"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
                Open User Management Console
              </a>
              <p className="text-sm text-gray-500 mt-2">
                Manage user roles, approvals, and permissions
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
