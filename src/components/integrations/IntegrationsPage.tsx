import { useState } from "react";

interface Integration {
  id: string;
  name: string;
  provider: string;
  status: "connected" | "disconnected" | "error";
  description: string;
}

export default function IntegrationsPage() {
  const [integrations] = useState<Integration[]>([
    {
      id: "1",
      name: "OpenAI GPT",
      provider: "OpenAI",
      status: "disconnected",
      description: "Connect to OpenAI's GPT models for text generation",
    },
    {
      id: "2",
      name: "Anthropic Claude",
      provider: "Anthropic",
      status: "disconnected",
      description: "Connect to Anthropic's Claude models for AI assistance",
    },
    {
      id: "3",
      name: "Google Gemini",
      provider: "Google",
      status: "disconnected",
      description: "Connect to Google's Gemini models for AI capabilities",
    },
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-green-100 text-green-800";
      case "error":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
        <p className="mt-1 text-sm text-gray-600">
          Connect to LLM providers and external services
        </p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-yellow-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Admin Configuration Required
            </h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>
                LLM integrations are managed by administrators. Contact your
                admin to configure API keys and budgets.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {integrations.map((integration) => (
          <div key={integration.id} className="bg-white shadow rounded-lg">
            <div className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-indigo-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        {integration.provider.charAt(0)}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      {integration.name}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {integration.description}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(integration.status)}`}
                  >
                    {integration.status}
                  </span>
                  <button
                    type="button"
                    className="bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 cursor-not-allowed"
                    disabled
                  >
                    Configure
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Integration Status
        </h2>
        <div className="space-y-3">
          <div className="text-sm">
            <span className="font-medium text-gray-900">
              Available Providers:
            </span>
            <span className="ml-2 text-gray-600">
              OpenAI, Anthropic, Google
            </span>
          </div>
          <div className="text-sm">
            <span className="font-medium text-gray-900">Admin Contact:</span>
            <span className="ml-2 text-gray-600">
              Contact your system administrator
            </span>
          </div>
          <div className="text-sm">
            <span className="font-medium text-gray-900">Budget Status:</span>
            <span className="ml-2 text-gray-600">Managed by admin</span>
          </div>
        </div>
      </div>
    </div>
  );
}
