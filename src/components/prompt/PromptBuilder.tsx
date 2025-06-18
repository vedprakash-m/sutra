import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/components/auth/AuthProvider";
import { llmApi, collectionsApi } from "@/services/api";
import PromptCoach from "./PromptCoach";

interface PromptData {
  title: string;
  description: string;
  content: string;
  collection_id?: string;
  variables?: Record<string, any>;
}

interface LLMOutput {
  provider: string;
  response: string;
  loading: boolean;
  error?: string;
}

export default function PromptBuilder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [promptData, setPromptData] = useState<PromptData>({
    title: "",
    description: "",
    content: "",
    variables: {},
  });
  const [selectedLLMs, setSelectedLLMs] = useState<string[]>(["openai"]);
  const [llmOutputs, setLlmOutputs] = useState<Record<string, LLMOutput>>({});
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Test prompt with selected LLMs
  const handleTestPrompt = async () => {
    if (!promptData.content.trim()) return;

    setIsTesting(true);
    const outputs: Record<string, LLMOutput> = {};

    // Initialize outputs for selected LLMs
    selectedLLMs.forEach((provider) => {
      outputs[provider] = { provider, response: "", loading: true };
    });
    setLlmOutputs(outputs);

    // Test each LLM in parallel
    const promises = selectedLLMs.map(async (provider) => {
      try {
        const response = (await llmApi.execute(
          promptData.content,
          provider,
          promptData.variables || {},
        )) as any;
        outputs[provider] = {
          provider,
          response:
            response?.data || response?.response || "No response received",
          loading: false,
        };
      } catch (error) {
        outputs[provider] = {
          provider,
          response: "",
          loading: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
      setLlmOutputs({ ...outputs });
    });

    await Promise.all(promises);
    setIsTesting(false);
  };

  // Save prompt as a collection for now (MVP approach)
  const handleSavePrompt = async () => {
    if (!promptData.title.trim() || !promptData.content.trim()) return;

    setIsSaving(true);
    try {
      const collection = {
        name: promptData.title,
        description: `${promptData.description}\n\nPrompt Content:\n${promptData.content}`,
        type: "private" as const,
        owner_id: user?.id || "dev-user",
        tags: ["prompt"],
      };

      if (id) {
        // Update existing collection
        await collectionsApi.update(id, collection);
      } else {
        // Create new collection
        await collectionsApi.create(collection);
      }

      navigate("/collections");
    } catch (error) {
      console.error("Error saving prompt:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const updatePromptData = (field: keyof PromptData, value: any) => {
    setPromptData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Prompt Builder</h1>
        <p className="mt-1 text-sm text-gray-600">
          Create and test AI prompts with multi-LLM comparison
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Prompt Details
            </h2>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="title"
                  className="block text-sm font-medium text-gray-700"
                >
                  Title
                </label>
                <input
                  type="text"
                  id="title"
                  value={promptData.title}
                  onChange={(e) => updatePromptData("title", e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Enter prompt title"
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
                  value={promptData.description}
                  onChange={(e) =>
                    updatePromptData("description", e.target.value)
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Describe what this prompt does"
                />
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Prompt Text
            </h2>
            <div>
              <textarea
                value={promptData.content}
                onChange={(e) => updatePromptData("content", e.target.value)}
                rows={10}
                className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Write your prompt here..."
              />
            </div>
          </div>

          <PromptCoach
            promptContent={promptData.content}
            intention={promptData.description}
            contextDetails={{}}
            onSuggestionApply={(suggestion) => {
              // Add suggestion to the end of prompt content
              updatePromptData(
                "content",
                promptData.content + "\n\n" + suggestion,
              );
            }}
          />

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              LLM Selection
            </h2>
            <div className="space-y-2">
              {["openai", "anthropic", "google"].map((llm) => (
                <label key={llm} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedLLMs.includes(llm)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedLLMs([...selectedLLMs, llm]);
                      } else {
                        setSelectedLLMs(selectedLLMs.filter((l) => l !== llm));
                      }
                    }}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700 capitalize">
                    {llm}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex space-x-4">
            <button
              type="button"
              onClick={handleTestPrompt}
              disabled={isTesting || !promptData.content.trim()}
              className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isTesting ? "Testing..." : "Test Prompt"}
            </button>
            <button
              type="button"
              onClick={handleSavePrompt}
              disabled={
                isSaving ||
                !promptData.title.trim() ||
                !promptData.content.trim()
              }
              className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? "Saving..." : "Save Prompt"}
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              LLM Outputs
            </h2>
            <div className="space-y-4">
              {selectedLLMs.map((llm) => {
                const output = llmOutputs[llm];
                return (
                  <div
                    key={llm}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <h3 className="text-sm font-medium text-gray-900 mb-2 capitalize">
                      {llm} Response
                    </h3>
                    <div className="bg-gray-50 rounded p-3 min-h-[100px] text-sm">
                      {output?.loading ? (
                        <div className="flex items-center text-gray-600">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                          Generating response...
                        </div>
                      ) : output?.error ? (
                        <div className="text-red-600">
                          Error: {output.error}
                        </div>
                      ) : output?.response ? (
                        <div className="text-gray-900 whitespace-pre-wrap">
                          {output.response}
                        </div>
                      ) : (
                        <div className="text-gray-600">
                          Click "Test Prompt" to see {llm} response
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Prompt Coach
            </h2>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-700">
                💡 AI-powered suggestions will appear here to help improve your
                prompt
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
