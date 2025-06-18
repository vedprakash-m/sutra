export default {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/test-setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "^@/services/api$": "<rootDir>/src/services/__mocks__/api.ts",
    "^../services/api$": "<rootDir>/src/services/__mocks__/api.ts",
  },
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        useESM: true,
        tsconfig: {
          jsx: "react-jsx",
        },
      },
    ],
  },
  // Handle ES modules and import.meta
  extensionsToTreatAsEsm: [".ts", ".tsx"],
  transformIgnorePatterns: [
    "node_modules/(?!(.*\\.mjs$))"
  ],
  globals: {
    // Mock import.meta for Vite compatibility
    "import.meta": {
      env: {
        VITE_API_URL: "http://localhost:7071/api",
        VITE_AUTH_DOMAIN: "test-domain",
        VITE_AUTH_CLIENT_ID: "test-client-id",
        MODE: "test",
        DEV: false,
        PROD: false,
      },
    },
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
  ],
  coverageReporters: ["text", "lcov", "html"],
  coverageDirectory: "coverage",
  coverageThreshold: {
    global: {
      branches: 5,
      functions: 5,
      lines: 5,
      statements: 5,
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
};
