import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// CDN optimization plugin
const cdnOptimizationPlugin = () => {
  return {
    name: "cdn-optimization",
    generateBundle(options, bundle) {
      // Generate asset manifest for CDN
      const manifest = {};
      for (const [fileName, chunk] of Object.entries(bundle)) {
        if (chunk.type === "asset" || chunk.type === "chunk") {
          const originalName = chunk.name || fileName.replace(/\.[^.]+$/, "");
          manifest[originalName] = fileName;
        }
      }

      // Write manifest file
      this.emitFile({
        type: "asset",
        fileName: "asset-manifest.json",
        source: JSON.stringify(manifest, null, 2),
      });

      // Add performance hints to HTML
      const indexChunk = bundle["index.html"];
      if (indexChunk && indexChunk.type === "asset") {
        let html = indexChunk.source as string;

        // Add resource hints
        const preloadLinks = [];
        for (const [fileName, chunk] of Object.entries(bundle)) {
          if (chunk.type === "chunk" && chunk.isEntry) {
            preloadLinks.push(
              `<link rel="preload" href="/${fileName}" as="script">`,
            );
          }
          if (chunk.type === "asset" && fileName.endsWith(".css")) {
            preloadLinks.push(
              `<link rel="preload" href="/${fileName}" as="style">`,
            );
          }
        }

        html = html.replace(
          "<head>",
          `<head>\n    ${preloadLinks.join("\n    ")}`,
        );

        indexChunk.source = html;
      }
    },
  };
};

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
        console.log(
          `🚀 Local API detected on port ${port}, using local backend`,
        );
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
    plugins: [react(), cdnOptimizationPlugin()],
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
      rollupOptions: {
        output: {
          // Asset naming with hash for cache busting
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split(".");
            const ext = info[info.length - 1];
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
              return `assets/images/[name].[hash][extname]`;
            }
            if (/css/i.test(ext)) {
              return `assets/css/[name].[hash][extname]`;
            }
            return `assets/[name].[hash][extname]`;
          },
          chunkFileNames: "assets/js/[name].[hash].js",
          entryFileNames: "assets/js/[name].[hash].js",
          // Code splitting for better caching
          manualChunks: {
            vendor: ["react", "react-dom"],
            routing: ["react-router-dom"],
            state: ["zustand", "react-query"],
          },
        },
      },
      // Enable compression
      minify: "terser",
      terserOptions: {
        compress: {
          drop_console: true,
          drop_debugger: true,
        },
      },
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
