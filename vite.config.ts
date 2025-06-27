import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { localAuthPlugin, getMockAuthHeaders } from "./src/dev/localAuthPlugin";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), localAuthPlugin()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
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
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
