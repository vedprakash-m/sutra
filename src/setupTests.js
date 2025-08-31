// Setup file for Jest to handle Vite's import.meta

// Mock import.meta for Jest environment
global.importMeta = {
  env: {
    VITE_API_URL: "http://localhost:7071/api",
    VITE_AUTH_DOMAIN: "test-domain",
    VITE_AUTH_CLIENT_ID: "test-client-id",
    VITE_ENTRA_CLIENT_ID: "test-entra-client-id",
    VITE_ENTRA_TENANT_ID: "common",
    NODE_ENV: "test",
    MODE: "test",
    DEV: false,
    PROD: false,
  },
};

// Define import.meta on globalThis to handle ES module syntax
Object.defineProperty(globalThis, "import", {
  value: {
    meta: global.importMeta,
  },
  configurable: true,
});

// Also define it directly on global for compatibility
global.import = { meta: global.importMeta };
