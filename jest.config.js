export default {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/test-setup.ts"],
  moduleNameMapper: {
    // Mock config to handle import.meta.env - must come before the general @/ pattern
    "^@/config$": "<rootDir>/src/config/__mocks__/index.ts",
    "^@/config/index$": "<rootDir>/src/config/__mocks__/index.ts",
    "^@/services/api$": "<rootDir>/src/services/__mocks__/api.ts",
    "^../services/api$": "<rootDir>/src/services/__mocks__/api.ts",
    "^../../services/api$": "<rootDir>/src/services/__mocks__/api.ts",
    "^@/(.*)$": "<rootDir>/src/$1",
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    // Mock MSAL libraries for Jest
    "^@azure/msal-react$": "<rootDir>/src/__mocks__/@azure/msal-react.tsx",
    "^@azure/msal-browser$": "<rootDir>/src/__mocks__/@azure/msal-browser.ts",
  },
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: {
          jsx: "react-jsx",
        },
        useESM: true,
      },
    ],
  },
  extensionsToTreatAsEsm: [".ts", ".tsx"],
  // Handle import.meta in Jest environment
  transformIgnorePatterns: ["node_modules/(?!(.*\\.mjs$))"],
  // Add environment setup to handle import.meta
  setupFiles: ["<rootDir>/src/setupTests.js"],
  // Set up test environment globals
  globals: {
    __DEV__: true,
  },
  moduleFileExtensions: ["ts", "tsx", "js", "jsx"],
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/test-setup.ts",
    "!src/main.tsx",
    "!src/vite-env.d.ts",
    // Include more components for better coverage
    "!src/components/**/*.stories.{ts,tsx}",
    "!src/**/__mocks__/**",
    // Exclude development-only files
    "!src/dev/**",
    "!src/test-utils.tsx",
    // Exclude test utilities and configuration files that don't need coverage
    "!src/test-utils/**",
    "!src/config/authConfig.ts",
    // Exclude MSAL provider as it's mostly Azure MSAL wrapper code
    "!src/components/auth/MSALAuthProvider.tsx", // Legacy compatibility file
  ],
  coverageReporters: ["text", "lcov", "html"],
  coverageDirectory: "coverage",
  coverageThreshold: {
    global: {
      branches: 67,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  testMatch: [
    "<rootDir>/src/**/__tests__/**/*.{ts,tsx}",
    "<rootDir>/src/**/*.{test,spec}.{ts,tsx}",
  ],
  testPathIgnorePatterns: ["/node_modules/", "/dist/", "/coverage/"],
  // Fast feedback for CI
  maxWorkers: process.env.CI ? "50%" : "100%",
  // Cache for faster subsequent runs
  cache: true,
  cacheDirectory: "<rootDir>/.jest-cache",
  // In CI, be more strict about warnings
  verbose: process.env.CI === "true",
};
