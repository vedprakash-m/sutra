import { getApiBaseUrl, isDevMode, isProdMode } from "../env";

// Mock environment variables
const originalEnv = process.env;

describe("Environment Utilities", () => {
  beforeEach(() => {
    // Reset environment
    process.env = { ...originalEnv };
    // Clear any window mocks
    delete (global as any).window;
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe("getApiBaseUrl", () => {
    it("should return test URL in test environment", () => {
      process.env.NODE_ENV = "test";
      process.env.VITE_API_URL = "http://test-api.com";
      expect(getApiBaseUrl()).toBe("http://test-api.com");
    });

    it("should return default test URL when no VITE_API_URL in test", () => {
      process.env.NODE_ENV = "test";
      delete process.env.VITE_API_URL;
      expect(getApiBaseUrl()).toBe("http://localhost:7071/api");
    });

    it("should return development URL in development", () => {
      process.env.NODE_ENV = "development";
      delete process.env.VITE_API_URL;
      expect(getApiBaseUrl()).toBe("http://localhost:7071/api");
    });

    it("should return production URL in production", () => {
      process.env.NODE_ENV = "production";
      delete process.env.VITE_API_URL;
      expect(getApiBaseUrl()).toBe(
        "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api",
      );
    });

    it("should return custom URL when VITE_API_URL is set", () => {
      process.env.NODE_ENV = "production";
      process.env.VITE_API_URL = "http://custom-api.com";
      expect(getApiBaseUrl()).toBe("http://custom-api.com");
    });

    it("should handle window with import.meta.env", () => {
      process.env.NODE_ENV = "production";
      delete process.env.VITE_API_URL;
      (global as any).window = {
        import: {
          meta: {
            env: {
              VITE_API_URL: "http://window-api.com",
              NODE_ENV: "production",
            },
          },
        },
      };
      expect(getApiBaseUrl()).toBe("http://window-api.com");
    });

    it("should fallback gracefully when import.meta fails", () => {
      process.env.NODE_ENV = "production";
      delete process.env.VITE_API_URL;
      (global as any).window = {
        import: null, // This will cause the access to fail
      };
      expect(getApiBaseUrl()).toBe(
        "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api",
      );
    });
  });

  describe("isDevMode", () => {
    it("should return false in test environment", () => {
      process.env.NODE_ENV = "test";
      expect(isDevMode()).toBe(false);
    });

    it("should return true in development environment", () => {
      process.env.NODE_ENV = "development";
      expect(isDevMode()).toBe(true);
    });

    it("should return false in production environment", () => {
      process.env.NODE_ENV = "production";
      expect(isDevMode()).toBe(false);
    });

    it("should handle window with import.meta.env.DEV", () => {
      process.env.NODE_ENV = "production";
      (global as any).window = {
        import: {
          meta: {
            env: {
              DEV: true,
            },
          },
        },
      };
      expect(isDevMode()).toBe(true);
    });

    it("should fallback gracefully when import.meta fails", () => {
      process.env.NODE_ENV = "development";
      (global as any).window = {
        import: null,
      };
      expect(isDevMode()).toBe(true);
    });
  });

  describe("isProdMode", () => {
    it("should return false in test environment", () => {
      process.env.NODE_ENV = "test";
      expect(isProdMode()).toBe(false);
    });

    it("should return false in development environment", () => {
      process.env.NODE_ENV = "development";
      expect(isProdMode()).toBe(false);
    });

    it("should return true in production environment", () => {
      process.env.NODE_ENV = "production";
      expect(isProdMode()).toBe(true);
    });

    it("should handle window with import.meta.env.PROD", () => {
      process.env.NODE_ENV = "development";
      (global as any).window = {
        import: {
          meta: {
            env: {
              PROD: true,
            },
          },
        },
      };
      expect(isProdMode()).toBe(true);
    });

    it("should fallback gracefully when import.meta fails", () => {
      process.env.NODE_ENV = "production";
      (global as any).window = {
        import: null,
      };
      expect(isProdMode()).toBe(true);
    });
  });
});
