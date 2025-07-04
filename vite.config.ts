import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(async () => {
  // Check if local API is available
  let useLocalAPI = false;
  let localAPIPort = 7071;
  const localPorts = [7071, 7072, 7073]; // Try multiple ports

  for (const port of localPorts) {
    try {
      const response = await fetch(`http://localhost:${port}/api/health`, {
        signal: AbortSignal.timeout(2000),
      });
      if (response.ok) {
        useLocalAPI = true;
        localAPIPort = port;
        console.log(`🚀 Local API detected on port ${port}, using local backend`);
        break;
      }
    } catch (error) {
      // Continue to next port
    }
  }

  if (!useLocalAPI) {
    console.log("⚠️ Local API not available, using production backend");
  }

  const baseConfig: any = {
    plugins: [react()],
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
        target: `http://localhost:${localAPIPort}`,
        changeOrigin: true,
        secure: false,
      },
    };
  } else {
    // When no local API, the frontend will use the production API directly
    console.log("📡 Frontend will connect directly to production API");
  }

  return baseConfig;
});
