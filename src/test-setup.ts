import "@testing-library/jest-dom";

// Mock environment variables for Jest tests
process.env.VITE_API_URL = "http://localhost:7071/api";
process.env.VITE_AUTH_DOMAIN = "test-domain";
process.env.VITE_AUTH_CLIENT_ID = "test-client-id";
process.env.NODE_ENV = "test";

// Mock Vite's import.meta for Jest tests
Object.defineProperty(globalThis, "import", {
  value: {
    meta: {
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
});

// Mock window.matchMedia for responsive components
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {}, // deprecated
    removeListener: () => {}, // deprecated
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock IntersectionObserver
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});
window.IntersectionObserver = mockIntersectionObserver;
window.IntersectionObserver.prototype.disconnect = jest.fn();
window.IntersectionObserver.prototype.observe = jest.fn();
window.IntersectionObserver.prototype.unobserve = jest.fn();
