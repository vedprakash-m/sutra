// Stub implementation for TypeScript compilation
export const useLLMCost = () => {
  return {
    totalCost: 0,
    addCost: (_cost: number) => {},
    resetCost: () => {},
    trackCost: (_cost: number, _model?: string, _operation?: string) => {},
  };
};
