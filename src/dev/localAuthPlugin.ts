import { Plugin } from "vite";

// Local development authentication mock
// This plugin provides a /.auth/me endpoint that mimics Azure Static Web Apps authentication
export interface MockUser {
  clientPrincipal: {
    identityProvider: string;
    userId: string;
    userDetails: string;
    userRoles: string[];
  } | null;
}

// Mock user profiles for local development
const mockUsers: Record<string, MockUser> = {
  admin: {
    clientPrincipal: {
      identityProvider: "aad",
      userId: "admin-user-local-dev",
      userDetails: "vedprakash.m@outlook.com",
      userRoles: ["authenticated"],
    },
  },
  user: {
    clientPrincipal: {
      identityProvider: "aad",
      userId: "regular-user-local-dev",
      userDetails: "user@example.com",
      userRoles: ["authenticated"],
    },
  },
  anonymous: {
    clientPrincipal: null,
  },
};

export function localAuthPlugin(): Plugin {
  return {
    name: "local-auth",
    configureServer(server) {
      server.middlewares.use("/.auth/me", (req, res, next) => {
        // Handle OPTIONS request for CORS
        if (req.method === "OPTIONS") {
          res.setHeader("Access-Control-Allow-Origin", "*");
          res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
          res.setHeader("Access-Control-Allow-Headers", "Content-Type");
          res.statusCode = 200;
          res.end();
          return;
        }

        if (req.method === "GET") {
          // Check multiple sources for auth mode
          let authMode = process.env.VITE_LOCAL_AUTH_MODE || "admin";

          // Allow runtime switching via localStorage (for development convenience)
          // Note: This would be passed via query param or custom header in a real scenario
          if (req.headers["x-local-auth-mode"]) {
            authMode = req.headers["x-local-auth-mode"] as string;
          }

          const userData = mockUsers[authMode] || mockUsers.anonymous;

          console.log(
            `🔧 Local auth mock: mode=${authMode}, user=${userData.clientPrincipal?.userDetails || "anonymous"}`,
          );

          res.setHeader("Content-Type", "application/json");
          res.setHeader("Access-Control-Allow-Origin", "*");
          res.statusCode = 200;
          res.end(JSON.stringify(userData));
          return;
        }

        next();
      });

      // Also handle the local auth mode switcher endpoint
      server.middlewares.use("/api/local-auth/switch", (req, res, next) => {
        if (req.method === "POST") {
          // This would typically switch the user mode, but for now we'll just return current state
          const authMode = process.env.VITE_LOCAL_AUTH_MODE || "admin";
          const userData = mockUsers[authMode] || mockUsers.anonymous;

          res.setHeader("Content-Type", "application/json");
          res.setHeader("Access-Control-Allow-Origin", "*");
          res.statusCode = 200;
          res.end(
            JSON.stringify({
              success: true,
              mode: authMode,
              user: userData,
              availableModes: Object.keys(mockUsers),
            }),
          );
          return;
        }

        next();
      });
    },
  };
}

// Utility function to set mock authentication headers for API requests
export function getMockAuthHeaders(mode?: string): Record<string, string> {
  const authMode = mode || process.env.VITE_LOCAL_AUTH_MODE || "admin";
  const userData = mockUsers[authMode];

  if (!userData.clientPrincipal) {
    return {}; // Anonymous user
  }

  // Mimic Azure Static Web Apps headers
  return {
    "x-ms-client-principal": Buffer.from(
      JSON.stringify(userData.clientPrincipal),
    ).toString("base64"),
    "x-ms-client-principal-id": userData.clientPrincipal.userId,
    "x-ms-client-principal-name": userData.clientPrincipal.userDetails,
    "x-ms-client-principal-idp": userData.clientPrincipal.identityProvider,
  };
}
