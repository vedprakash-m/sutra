import baseConfig from "./jest.config.js";

const forgeTestPatterns = [
  "<rootDir>/src/components/forge/**/__tests__/**/*.{ts,tsx}",
  "<rootDir>/src/components/forge/**/*.{test,spec}.{ts,tsx}",
  "<rootDir>/src/stores/forgeStore.test.ts",
];

export default {
  ...baseConfig,
  testMatch: forgeTestPatterns,
  collectCoverageFrom: [
    "src/components/forge/ForgePage.tsx",
    "src/components/forge/ForgeProjectDetails.tsx",
    "src/components/forge/ForgeProjectCard.tsx",
    "src/components/forge/ForgeExportButton.tsx",
    "src/components/forge/LLMProviderSelector.tsx",
    "src/components/forge/ProgressIndicator.tsx",
    "src/components/forge/QualityGate.tsx",
    "src/stores/forgeStore.ts",
    "!src/**/*.d.ts",
  ],
  coverageDirectory: "coverage/forge",
  coverageThreshold: {
    global: {
      branches: 65,
      functions: 75,
      lines: 75,
      statements: 75,
    },
  },
};
