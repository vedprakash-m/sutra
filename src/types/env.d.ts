/// <reference types="vite/client" />

declare global {
  namespace NodeJS {
    interface ProcessEnv {
      NODE_ENV: "development" | "production" | "test";
      VITE_API_URL?: string;
      VITE_AUTH_DOMAIN?: string;
      VITE_AUTH_CLIENT_ID?: string;
    }
  }

  interface ImportMetaEnv {
    readonly VITE_API_URL?: string;
    readonly VITE_AUTH_DOMAIN?: string;
    readonly VITE_AUTH_CLIENT_ID?: string;
    readonly DEV: boolean;
    readonly PROD: boolean;
    readonly MODE: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }

  // For Node.js environment variables
  var process: {
    env: NodeJS.ProcessEnv;
  };

  // For global fetch and other browser APIs
  var global: typeof globalThis;
}

export {};
