import { useState } from "react";
import { useAuth } from "./MSALAuthProvider";

export function GuestLogin() {
  const { loginAsGuest, isLoading } = useAuth();
  const [isStarting, setIsStarting] = useState(false);

  const handleGuestLogin = async () => {
    setIsStarting(true);
    try {
      await loginAsGuest();
    } catch (error) {
      console.error("Guest login failed:", error);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 p-6 rounded-lg border border-blue-200">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          Try Sutra as a Guest
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Test our AI tools with limited usage - no signup required!
        </p>

        <div className="bg-white p-4 rounded-md border border-blue-100 mb-4">
          <h4 className="font-medium text-gray-700 mb-2">Guest Features:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• 5 AI prompts per day</li>
            <li>• 10 prompt templates</li>
            <li>• 3 collections per session</li>
            <li>• 2 playbooks per session</li>
            <li>• 24-hour session duration</li>
          </ul>
        </div>

        <button
          onClick={handleGuestLogin}
          disabled={isLoading || isStarting}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isStarting ? "Starting Guest Session..." : "Start as Guest"}
        </button>

        <p className="text-xs text-gray-500 mt-3">
          Want unlimited access?{" "}
          <span className="text-blue-600 font-medium">Sign up for free</span>
        </p>
      </div>
    </div>
  );
}

export function GuestUsageIndicator() {
  const { guestSession, isGuest } = useAuth();

  if (!isGuest || !guestSession) return null;

  const { usage, limits, remaining } = guestSession;

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
          <span className="text-sm font-medium text-yellow-800">
            Guest Mode
          </span>
        </div>
        <span className="text-xs text-yellow-600">Session Active</span>
      </div>

      <div className="mt-2 space-y-1">
        <div className="flex justify-between text-xs text-yellow-700">
          <span>AI Calls:</span>
          <span>
            {usage.llm_calls || 0} / {limits.llm_calls_per_day || 5}
          </span>
        </div>
        <div className="flex justify-between text-xs text-yellow-700">
          <span>Prompts:</span>
          <span>
            {usage.prompts_created || 0} / {limits.prompts_per_day || 10}
          </span>
        </div>
      </div>

      {(remaining.llm_calls || 0) <= 1 && (
        <div className="mt-2 p-2 bg-yellow-100 rounded border border-yellow-300">
          <p className="text-xs text-yellow-800">
            ⚠️ Almost at your daily limit!
            <span className="font-medium"> Sign up for unlimited access.</span>
          </p>
        </div>
      )}
    </div>
  );
}
