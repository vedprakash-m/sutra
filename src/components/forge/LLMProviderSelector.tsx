/**
 * LLM Provider Selector Component
 * Allows users to choose which AI provider and model to use for Forge operations.
 * Reads/writes provider state from the forgeStore.
 */
import React from "react";
import { useForgeStore } from "@/stores/forgeStore";
import {
  LLM_PROVIDERS,
  type LLMProviderName,
  type LLMModelOption,
} from "@/types/forge";

const COST_TIER_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

const COST_TIER_LABELS: Record<string, string> = {
  low: "$",
  medium: "$$",
  high: "$$$",
};

export const LLMProviderSelector: React.FC = () => {
  const { selectedProvider, selectedModel, setLLMProvider } = useForgeStore();

  const currentProviderInfo = LLM_PROVIDERS.find(
    (p) => p.name === selectedProvider,
  );
  const availableModels: LLMModelOption[] = currentProviderInfo?.models || [];

  const handleProviderChange = (provider: LLMProviderName) => {
    setLLMProvider(provider);
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLLMProvider(selectedProvider, e.target.value);
  };

  const currentModel = availableModels.find((m) => m.id === selectedModel);

  return (
    <div className="flex items-center gap-3">
      {/* Provider tabs */}
      <div className="flex rounded-lg border border-gray-200 bg-gray-50 p-0.5">
        {LLM_PROVIDERS.filter((p) => p.isAvailable).map((provider) => (
          <button
            key={provider.name}
            onClick={() => handleProviderChange(provider.name)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              selectedProvider === provider.name
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
            title={provider.displayName}
          >
            {provider.displayName}
          </button>
        ))}
      </div>

      {/* Model dropdown */}
      <select
        value={selectedModel}
        onChange={handleModelChange}
        className="text-xs border border-gray-200 rounded-md px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        {availableModels.map((model) => (
          <option key={model.id} value={model.id}>
            {model.displayName}
          </option>
        ))}
      </select>

      {/* Cost indicator */}
      {currentModel && (
        <span
          className={`text-xs px-1.5 py-0.5 rounded font-medium ${COST_TIER_COLORS[currentModel.costTier]}`}
          title={`Cost tier: ${currentModel.costTier}`}
        >
          {COST_TIER_LABELS[currentModel.costTier]}
        </span>
      )}
    </div>
  );
};
