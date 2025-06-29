import "@testing-library/jest-dom";
import { configure } from "@testing-library/react";

// Configure Testing Library to use React's act instead of ReactDOMTestUtils.act
configure({ asyncUtilTimeout: 2000 });

// Mock environment variables for Jest tests
process.env.VITE_API_URL = "http://localhost:7071/api";
process.env.VITE_AUTH_DOMAIN = "test-domain";
process.env.VITE_AUTH_CLIENT_ID = "test-client-id";
process.env.NODE_ENV = "test";

// Suppress specific console warnings in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.error = (...args: any[]) => {
  // Suppress React Router future flag warnings and React act warnings in tests
  if (
    typeof args[0] === "string" &&
    (args[0].includes("React Router Future Flag Warning") ||
      args[0].includes("ReactDOMTestUtils.act` is deprecated") ||
      args[0].includes("Warning: An update to") ||
      args[0].includes("act(...)"))
  ) {
    return;
  }
  originalConsoleError.apply(console, args);
};

console.warn = (...args: any[]) => {
  // Suppress React Router deprecation warnings in tests
  if (
    typeof args[0] === "string" &&
    (args[0].includes("React Router Future Flag Warning") ||
      args[0].includes("ReactDOMTestUtils"))
  ) {
    return;
  }
  originalConsoleWarn.apply(console, args);
};

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

// Mock fetch for all tests
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(""),
    headers: new Headers(),
  }),
) as jest.Mock;

// Mock window.alert to prevent JSDOM errors
global.alert = jest.fn();
