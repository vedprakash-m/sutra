export default {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/test-setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "^@/services/api$": "<rootDir>/src/services/__mocks__/api.ts",
    "^../services/api$": "<rootDir>/src/services/__mocks__/api.ts",
    "^../../services/api$": "<rootDir>/src/services/__mocks__/api.ts",
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
  globals: {
    "ts-jest": {
      useESM: true,
    },
  },
  // Handle import.meta in Jest environment
  transformIgnorePatterns: ["node_modules/(?!(.*\\.mjs$))"],
  // Add environment setup to handle import.meta
  setupFiles: ["<rootDir>/src/setupTests.js"],
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
  ],
  coverageReporters: ["text", "lcov", "html"],
  coverageDirectory: "coverage",
  coverageThreshold: {
    global: {
      branches: 70,
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
