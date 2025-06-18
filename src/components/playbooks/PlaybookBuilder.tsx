import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/components/auth/AuthProvider";
import { playbooksApi } from "@/services/api";

interface PlaybookStep {
  id: string;
  type: "prompt" | "review" | "variable";
  content: string;
  variables?: Record<string, any>;
  order: number;
}

interface PlaybookData {
  name: string;
  description: string;
  steps: PlaybookStep[];
  visibility: "private" | "shared";
}

export default function PlaybookBuilder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [playbookData, setPlaybookData] = useState<PlaybookData>({
    name: "",
    description: "",
    steps: [],
    visibility: "private",
  });
  const [isSaving, setIsSaving] = useState(false);

  const addStep = (type: PlaybookStep["type"]) => {
    const newStep: PlaybookStep = {
      id: `step-${Date.now()}`,
      type,
      content: "",
      order: playbookData.steps.length,
      variables: {},
    };
    setPlaybookData((prev) => ({
      ...prev,
      steps: [...prev.steps, newStep],
    }));
  };

  const updateStep = (stepId: string, updates: Partial<PlaybookStep>) => {
    setPlaybookData((prev) => ({
      ...prev,
      steps: prev.steps.map((step) =>
        step.id === stepId ? { ...step, ...updates } : step,
      ),
    }));
  };

  const removeStep = (stepId: string) => {
    setPlaybookData((prev) => ({
      ...prev,
      steps: prev.steps.filter((step) => step.id !== stepId),
    }));
  };

  const handleSavePlaybook = async () => {
    if (!playbookData.name.trim()) return;

    setIsSaving(true);
    try {
      const playbook = {
        name: playbookData.name,
        description: playbookData.description,
        steps: playbookData.steps,
        creator_id: user?.id || "dev-user",
        visibility: playbookData.visibility,
      };

      if (id) {
        await playbooksApi.update(id, playbook);
      } else {
        await playbooksApi.create(playbook);
      }

      navigate("/collections");
    } catch (error) {
      console.error("Error saving playbook:", error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Playbook Builder</h1>
          <p className="mt-1 text-sm text-gray-600">
            Create linear AI workflows and automation playbooks
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => navigate(`/playbooks/${id || "new"}/run`)}
            disabled={!playbookData.name.trim() || !id}
            className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
          >
            Run Playbook
          </button>
          <button
            onClick={handleSavePlaybook}
            disabled={isSaving || !playbookData.name.trim()}
            className="bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isSaving ? "Saving..." : "Save Playbook"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Playbook Details */}
        <div className="lg:col-span-1">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Playbook Details
            </h2>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="name"
                  className="block text-sm font-medium text-gray-700"
                >
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={playbookData.name}
                  onChange={(e) =>
                    setPlaybookData((prev) => ({
                      ...prev,
                      name: e.target.value,
                    }))
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Enter playbook name"
                />
              </div>
              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-medium text-gray-700"
                >
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  value={playbookData.description}
                  onChange={(e) =>
                    setPlaybookData((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Describe what this playbook does"
                />
              </div>
              <div>
                <label
                  htmlFor="visibility"
                  className="block text-sm font-medium text-gray-700"
                >
                  Visibility
                </label>
                <select
                  id="visibility"
                  value={playbookData.visibility}
                  onChange={(e) =>
                    setPlaybookData((prev) => ({
                      ...prev,
                      visibility: e.target.value as "private" | "shared",
                    }))
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="private">Private</option>
                  <option value="shared">Shared</option>
                </select>
              </div>
            </div>

            {/* Add Step Buttons */}
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Add Step
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => addStep("prompt")}
                  className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
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
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  Prompt Step
                </button>
                <button
                  onClick={() => addStep("review")}
                  className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
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
                      d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                  Review Step
                </button>
                <button
                  onClick={() => addStep("variable")}
                  className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
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
                      d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                    />
                  </svg>
                  Variable Step
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Workflow Canvas */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Workflow Steps
            </h2>

            {playbookData.steps.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-12 h-12 bg-purple-500 rounded-md flex items-center justify-center mx-auto">
                  <span className="text-white text-lg font-medium">W</span>
                </div>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  Build Your First Workflow
                </h3>
                <p className="mt-2 text-sm text-gray-500 max-w-md mx-auto">
                  Add steps to create a workflow. Steps will be executed in
                  order from top to bottom.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {playbookData.steps.map((step, index) => (
                  <div
                    key={step.id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <span className="bg-gray-100 text-gray-800 text-xs font-medium px-2.5 py-0.5 rounded capitalize">
                          {step.type}
                        </span>
                        <span className="ml-2 text-sm text-gray-500">
                          Step {index + 1}
                        </span>
                      </div>
                      <button
                        onClick={() => removeStep(step.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>
                    <textarea
                      value={step.content}
                      onChange={(e) =>
                        updateStep(step.id, { content: e.target.value })
                      }
                      placeholder={`Enter ${step.type} content...`}
                      rows={3}
                      className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
