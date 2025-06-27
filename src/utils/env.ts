// Utility functions to get environment variables that work in both runtime and Jest
export function getApiBaseUrl(): string {
  // Check if we're in a test environment first
  if (typeof process !== "undefined" && process.env.NODE_ENV === "test") {
    return process.env.VITE_API_URL || "http://localhost:7071/api";
  }

  // Try to access import.meta.env safely
  let viteApiUrl: string | undefined;
  let nodeEnv: string | undefined;

  try {
    // This will work in Vite/browser environment
    if (
      typeof window !== "undefined" &&
      "import" in window &&
      (window as any).import?.meta
    ) {
      viteApiUrl = (window as any).import?.meta?.env?.VITE_API_URL;
      nodeEnv = (window as any).import?.meta?.env?.NODE_ENV;
    } else {
      // Fallback to process.env
      viteApiUrl = process.env.VITE_API_URL;
      nodeEnv = process.env.NODE_ENV;
    }
  } catch {
    // If import.meta fails, use process.env
    viteApiUrl = process.env.VITE_API_URL;
    nodeEnv = process.env.NODE_ENV;
  }

  if (viteApiUrl) {
    return viteApiUrl;
  }

  if (nodeEnv === "development" || nodeEnv === "test") {
    return "http://localhost:7071/api";
  }

  return "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api";
}

export function isDevMode(): boolean {
  if (typeof process !== "undefined" && process.env.NODE_ENV === "test") {
    return false; // Test environment is not dev mode
  }

  try {
    if (
      typeof window !== "undefined" &&
      "import" in window &&
      (window as any).import?.meta
    ) {
      return (window as any).import?.meta?.env?.DEV || false;
    }
    return process.env.NODE_ENV === "development";
  } catch {
    return process.env.NODE_ENV === "development";
  }
}

export function isProdMode(): boolean {
  if (typeof process !== "undefined" && process.env.NODE_ENV === "test") {
    return false; // Test environment is not production mode
  }

  try {
    if (
      typeof window !== "undefined" &&
      "import" in window &&
      (window as any).import?.meta
    ) {
      return (window as any).import?.meta?.env?.PROD || false;
    }
    return process.env.NODE_ENV === "production";
  } catch {
    return process.env.NODE_ENV === "production";
  }
}
