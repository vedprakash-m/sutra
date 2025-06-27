import React, { useState } from "react";
import { getApiBaseUrl } from "../../utils/env";

interface AnonymousTestResponse {
  choices: Array<{ text: string }>;
  anonymous_info: {
    remaining_calls: number;
    daily_limit: number;
    signup_message: string;
  };
}

export function AnonymousLLMTest() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState<AnonymousTestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState<{
    remaining_calls: number;
    daily_limit: number;
  } | null>(null);

  const handleTest = async () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt to test");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Get API base URL from environment or use default
      const apiBaseUrl = getApiBaseUrl();

      const response = await fetch(`${apiBaseUrl}/anonymous/llm/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      const data = await response.json();

      if (response.ok) {
        setResponse(data);
        setUsage({
          remaining_calls: data.anonymous_info.remaining_calls,
          daily_limit: data.anonymous_info.daily_limit,
        });
      } else {
        if (response.status === 429) {
          setError(
            data.message ||
              "Daily limit exceeded. Please sign up for unlimited access.",
          );
        } else if (
          response.status === 400 &&
          data.error === "prompt_too_long"
        ) {
          setError(
            `Prompt too long (${data.current_length} chars). Anonymous users limited to ${data.max_length} characters.`,
          );
        } else {
          setError(data.error || data.message || "Failed to process request");
        }
      }
    } catch (err) {
      console.error("Anonymous LLM test error:", err);
      setError(
        `Network error: ${err instanceof Error ? err.message : "Please try again."}`,
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      handleTest();
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 border border-blue-200 rounded-lg p-6 space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          🚀 Try Sutra AI - No Login Required!
        </h3>
        <p className="text-sm text-gray-600">
          Test our AI capabilities with a free anonymous trial
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label
            htmlFor="anonymous-prompt"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Enter your prompt (max 500 characters):
          </label>
          <div className="relative">
            <textarea
              id="anonymous-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., Write a short poem about technology..."
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm resize-none"
              rows={3}
              maxLength={500}
              disabled={loading}
            />
            <div className="absolute bottom-2 right-2 text-xs text-gray-400">
              {prompt.length}/500
            </div>
          </div>
        </div>

        <button
          onClick={handleTest}
          disabled={loading || !prompt.trim()}
          className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Processing...
            </span>
          ) : (
            "Test AI Response"
          )}
        </button>

        {usage && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-center">
            <p className="text-sm text-blue-800">
              <span className="font-semibold">{usage.remaining_calls}</span> of{" "}
              <span className="font-semibold">{usage.daily_limit}</span> free
              calls remaining today
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {response && (
          <div className="bg-white border border-gray-200 rounded-md p-4 space-y-3">
            <h4 className="font-semibold text-gray-900">AI Response:</h4>
            <div className="bg-gray-50 p-3 rounded text-sm text-gray-800 whitespace-pre-wrap">
              {response.choices[0]?.text}
            </div>
            <div className="text-center bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-md p-3">
              <p className="text-sm text-indigo-800 font-medium">
                {response.anonymous_info.signup_message}
              </p>
              <p className="text-xs text-indigo-600 mt-1">
                Sign up to unlock unlimited calls, better models, and more
                features!
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="text-center pt-2">
        <p className="text-xs text-gray-500">
          ⚡ Powered by GPT-3.5 Turbo • 🔒 No data stored • 📊 IP-based rate
          limiting
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Press Ctrl/Cmd + Enter to submit
        </p>
      </div>
    </div>
  );
}
