import { useState, useEffect } from "react";

interface GuestLimits {
  llm_calls_per_day: number;
  prompts_per_day: number;
  collections_per_session: number;
  playbooks_per_session: number;
  session_duration_hours: number;
  enabled: boolean;
}

interface GuestSettings {
  id: string;
  limits: GuestLimits;
  created_at: string;
  updated_at: string;
  updated_by?: string;
}

export function GuestUserSettings() {
  const [settings, setSettings] = useState<GuestSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch("/api/admin/guest/settings");
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      } else {
        setError("Failed to load guest settings");
      }
    } catch (err) {
      setError("Error loading settings");
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch("/api/admin/guest/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ limits: settings.limits }),
      });

      if (response.ok) {
        const updatedSettings = await response.json();
        setSettings(updatedSettings);
        setSuccessMessage("Guest user settings updated successfully!");
        setTimeout(() => setSuccessMessage(null), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Failed to update settings");
      }
    } catch (err) {
      setError("Error saving settings");
    } finally {
      setSaving(false);
    }
  };

  const updateLimit = (key: keyof GuestLimits, value: number | boolean) => {
    if (!settings) return;

    setSettings({
      ...settings,
      limits: {
        ...settings.limits,
        [key]: value,
      },
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div
          className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"
          data-testid="loading-spinner"
        ></div>
        <span className="ml-2">Loading guest settings...</span>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Failed to load guest user settings</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">
          Anonymous Guest User Settings
        </h3>
        <p className="mt-1 text-sm text-gray-600">
          Configure limits for anonymous users who test Sutra without signing up
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Enable/Disable Anonymous Access */}
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-900">
              Anonymous Access
            </h4>
            <p className="text-sm text-gray-600">
              Allow unauthenticated users to test LLM capabilities
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.limits.enabled}
              onChange={(e) => updateLimit("enabled", e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
          </label>
        </div>

        {/* Daily LLM Call Limit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Daily LLM Calls Limit
          </label>
          <div className="flex items-center space-x-4">
            <input
              type="number"
              min="0"
              max="100"
              value={settings.limits.llm_calls_per_day}
              onChange={(e) =>
                updateLimit("llm_calls_per_day", parseInt(e.target.value) || 0)
              }
              className="block w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            <span className="text-sm text-gray-600">
              calls per IP address per day
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-500">
            Anonymous users are tracked by IP address. This is the total number
            of LLM calls they can make per day.
          </p>
        </div>

        {/* Other Limits */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Daily Prompt Creation Limit
            </label>
            <input
              type="number"
              min="0"
              max="50"
              value={settings.limits.prompts_per_day}
              onChange={(e) =>
                updateLimit("prompts_per_day", parseInt(e.target.value) || 0)
              }
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              For guest users who create sessions
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Collections per Session
            </label>
            <input
              type="number"
              min="0"
              max="10"
              value={settings.limits.collections_per_session}
              onChange={(e) =>
                updateLimit(
                  "collections_per_session",
                  parseInt(e.target.value) || 0,
                )
              }
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Playbooks per Session
            </label>
            <input
              type="number"
              min="0"
              max="10"
              value={settings.limits.playbooks_per_session}
              onChange={(e) =>
                updateLimit(
                  "playbooks_per_session",
                  parseInt(e.target.value) || 0,
                )
              }
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Session Duration (hours)
            </label>
            <input
              type="number"
              min="1"
              max="168"
              value={settings.limits.session_duration_hours}
              onChange={(e) =>
                updateLimit(
                  "session_duration_hours",
                  parseInt(e.target.value) || 24,
                )
              }
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Anonymous User Info Panel */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            📊 Anonymous User Features
          </h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• IP-based rate limiting (no cookies or sessions required)</li>
            <li>• Limited to GPT-3.5 Turbo model only</li>
            <li>• Maximum 500 characters per prompt</li>
            <li>• Maximum 100 tokens per response</li>
            <li>• Cannot save prompts, collections, or playbooks</li>
            <li>• Resets daily at midnight UTC</li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            {settings.updated_at && (
              <span>
                Last updated: {new Date(settings.updated_at).toLocaleString()}
                {settings.updated_by && ` by ${settings.updated_by}`}
              </span>
            )}
          </div>

          <button
            onClick={saveSettings}
            disabled={saving}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>

        {/* Messages */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {successMessage && (
          <div className="bg-green-50 border border-green-200 rounded-md p-3">
            <p className="text-sm text-green-800">{successMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
}
