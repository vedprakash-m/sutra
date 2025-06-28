import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { localAuthPlugin, getMockAuthHeaders } from "./src/dev/localAuthPlugin";

// https://vitejs.dev/config/
export default defineConfig(async () => {
  // Check if local API is available
  let useLocalAPI = false;
  try {
    const response = await fetch("http://localhost:7071/api/health", {
      signal: AbortSignal.timeout(2000),
    });
    useLocalAPI = response.ok;
    console.log("🚀 Local API detected, using local backend");
  } catch (error) {
    console.log("⚠️ Local API not available, using production backend");
    useLocalAPI = false;
  }

  const baseConfig: any = {
    plugins: [react(), localAuthPlugin()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5173,
    },
    build: {
      outDir: "dist",
      sourcemap: true,
    },
    define: {
      // Pass backend mode to the frontend
      "import.meta.env.VITE_USE_LOCAL_API": JSON.stringify(useLocalAPI),
    },
  };

  // Add proxy only if local API is available
  if (useLocalAPI) {
    baseConfig.server.proxy = {
      "/api": {
        target: "http://localhost:7071",
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq, req) => {
            // Forward all x-ms-* headers (Azure Static Web Apps headers)
            Object.keys(req.headers).forEach((header) => {
              if (header.startsWith("x-ms-")) {
                proxyReq.setHeader(header, req.headers[header]);
              }
            });

            // Add mock authentication headers for local development
            const authMode = process.env.VITE_LOCAL_AUTH_MODE || "admin";
            const mockHeaders = getMockAuthHeaders(authMode);
            Object.entries(mockHeaders).forEach(([key, value]) => {
              proxyReq.setHeader(key, value);
            });
          });
        },
      },
    };
  } else {
    // When no local API, the frontend will use the production API directly
    console.log("📡 Frontend will connect directly to production API");
  }

  return baseConfig;
});
