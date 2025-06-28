import {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
} from "react";

interface User {
  id: string;
  email: string;
  name: string;
  role: string; // Single role: "user", "admin", or "guest"
}

interface GuestSession {
  id: string;
  usage: Record<string, number>;
  limits: Record<string, number>;
  remaining: Record<string, number>;
  active: boolean;
}

interface AuthContextType {
  user: User | null;
  guestSession: GuestSession | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  token: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

// Static Web Apps authentication info interface
interface StaticWebAppsUser {
  clientPrincipal: {
    identityProvider: string;
    userId: string;
    userDetails: string;
    userRoles: string[];
    claims: Array<{ typ: string; val: string }>;
  } | null;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [guestSession, setGuestSession] = useState<GuestSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  const isAuthenticated = !!user;
  const isGuest = user?.role === "guest";
  const isAdmin = user?.role === "admin";

  // Initialize auth state from Static Web Apps or local development mock
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Detect environment
        const isProduction = window.location.hostname.includes(
          "azurestaticapps.net",
        );
        const isLocalDev =
          process.env.NODE_ENV === "development" ||
          window.location.hostname === "localhost" ||
          window.location.hostname === "127.0.0.1";

        console.log(`🔍 Environment detection:`, { isProduction, isLocalDev });

        // Try Static Web Apps authentication (works in both production and local mock)
        const response = await fetch("/.auth/me");

        if (response.ok) {
          const authInfo: StaticWebAppsUser = await response.json();
          console.log("Authentication info:", authInfo);

          if (authInfo.clientPrincipal) {
            const principal = authInfo.clientPrincipal;

            // Extract user information from claims or userDetails
            const email = principal.userDetails;

            // Extract name from claims or derive from email
            let name = principal.claims?.find(
              (c) =>
                c.typ ===
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
            )?.val;

            // If no name claim, extract name from email
            if (!name && email) {
              const emailName = email.split("@")[0];
              name = emailName
                .split(/[._-]/)
                .map(
                  (part) =>
                    part.charAt(0).toUpperCase() + part.slice(1).toLowerCase(),
                )
                .join(" ");
            }

            // Final fallback
            if (!name) {
              name = email || "User";
            }

            // Determine user role - check multiple sources
            let userRole = "user";

            console.log(`🔍 Role determination for ${email}:`, {
              userRoles: principal.userRoles,
              userDetails: principal.userDetails,
              userId: principal.userId,
              isLocalDev,
            });

            // Check Azure Static Web Apps roles first
            if (principal.userRoles?.includes("admin")) {
              userRole = "admin";
              console.log("✅ Admin role found in Azure userRoles");
            }

            // Override for specific admin user (both environments)
            if (email === "vedprakash.m@outlook.com") {
              userRole = "admin";
              console.log("🔑 Admin override for primary admin user");
            }

            // Fallback: Get role from backend API
            if (!principal.userRoles?.includes("admin")) {
              try {
                console.log("🔄 Fetching role from backend /getroles...");

                // Create authentication headers using the same logic as ApiService
                const authHeaders: Record<string, string> = {
                  "Content-Type": "application/json",
                  "x-ms-client-principal": btoa(JSON.stringify(principal)),
                  "x-ms-client-principal-id": principal.userId,
                  "x-ms-client-principal-name": principal.userDetails,
                  "x-ms-client-principal-idp": principal.identityProvider,
                };

                const roleResponse = await fetch("/api/getroles", {
                  method: "GET",
                  headers: authHeaders,
                });

                if (roleResponse.ok) {
                  const roleData = await roleResponse.json();
                  console.log("Backend role response:", roleData);

                  if (
                    roleData.roles &&
                    Array.isArray(roleData.roles) &&
                    roleData.roles.includes("admin")
                  ) {
                    userRole = "admin";
                    console.log("✅ Admin role confirmed by backend API");
                  }
                } else {
                  console.warn(
                    "Backend role API response not ok:",
                    roleResponse.status,
                  );
                }
              } catch (roleError) {
                console.warn(
                  "Could not fetch user role from backend:",
                  roleError,
                );
              }
            }

            const authUser: User = {
              id: principal.userId,
              email: email,
              name: name,
              role: userRole,
            };

            console.log("✅ Authenticated user created:", authUser);
            setUser(authUser);
            setToken(isLocalDev ? "local-dev-token" : "static-web-apps-token");
            setIsLoading(false);
            return;
          } else {
            console.log("No clientPrincipal found - user is anonymous");
          }
        } else {
          console.log(
            `Auth endpoint response not ok: ${response.status} ${response.statusText}`,
          );

          // In local development, if no auth mock is set, default to anonymous
          if (isLocalDev) {
            console.log(
              "🔧 Local development - no auth configured, remaining anonymous",
            );
          }
        }

        // If we reach here, user is not authenticated
        console.log("No authenticated user found");
      } catch (error) {
        console.error("Failed to check auth status:", error);

        // In local development, provide more helpful error messages
        if (process.env.NODE_ENV === "development") {
          console.log(
            "💡 Local development tip: Set VITE_LOCAL_AUTH_MODE=admin to test admin features",
          );
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const loginAsGuest = async () => {
    try {
      setIsLoading(true);

      // Get or create guest session using the existing API
      const response = await fetch("/api/guest/session", {
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        const sessionId =
          response.headers.get("X-Guest-Session-Id") || data.session?.id;

        // Create guest user
        const guestUser: User = {
          id: data.session.id,
          email: "guest@sutra.app",
          name: "Guest User",
          role: "guest",
        };

        const guestSessionData: GuestSession = {
          id: data.session.id,
          usage: data.usage || {},
          limits: data.limits || {},
          remaining: data.remaining || {},
          active: data.session.active,
        };

        setUser(guestUser);
        setGuestSession(guestSessionData);
        setToken(`guest-${sessionId}`);

        // Store session ID for future requests
        if (sessionId) {
          localStorage.setItem("sutra_guest_session_id", sessionId);
        }

        console.log("✅ Guest session created:", {
          guestUser,
          guestSessionData,
        });
      } else {
        throw new Error("Failed to create guest session");
      }
    } catch (error) {
      console.error("Failed to login as guest:", error);
      alert("Failed to start guest session. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const login = async () => {
    // Check if we're in a development environment
    const isLocalDev =
      process.env.NODE_ENV === "development" ||
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1";

    if (isLocalDev) {
      // Development mode: Show options to switch auth mode
      const authMode = prompt(
        "Local Development Authentication:\n\n" +
          "Enter auth mode:\n" +
          "- 'admin' for admin user\n" +
          "- 'user' for regular user\n" +
          "- 'anonymous' for anonymous access\n\n" +
          "Current mode: " +
          (localStorage.getItem("vite_local_auth_mode") || "anonymous"),
        localStorage.getItem("vite_local_auth_mode") || "admin",
      );

      if (authMode && ["admin", "user", "anonymous"].includes(authMode)) {
        localStorage.setItem("vite_local_auth_mode", authMode);

        // Set environment variable for the mock
        if (window.location.search.includes("reload=false")) {
          // Just update state without reload for testing
          window.location.search = "";
        } else {
          // Reload to pick up new auth mode
          window.location.reload();
        }
      }
    } else {
      // Production: Redirect to Azure Static Web Apps authentication endpoint
      try {
        // First check if auth system is available by testing /.auth/me
        const authTestResponse = await fetch("/.auth/me");

        if (!authTestResponse.ok) {
          // Authentication system is not configured - show helpful error
          alert(
            "Authentication system is not properly configured in Azure Static Web Apps.\n\n" +
              "Please contact the administrator to:\n" +
              "1. Enable authentication in Azure Portal\n" +
              "2. Configure Microsoft Entra External ID\n" +
              "3. Set up the required environment variables",
          );
          return;
        }

        // Try to get available providers
        const authProvidersResponse = await fetch("/.auth/providers");
        if (authProvidersResponse.ok) {
          const providers = await authProvidersResponse.json();
          console.log("Available auth providers:", providers);

          // Look for Microsoft/Azure AD provider
          const microsoftProvider = providers.find(
            (p: any) =>
              p.name?.toLowerCase().includes("microsoft") ||
              p.name?.toLowerCase().includes("aad") ||
              p.name?.toLowerCase().includes("azure"),
          );

          if (microsoftProvider) {
            window.location.href = `/.auth/login/${microsoftProvider.name}`;
            return;
          }
        }

        // Try different provider names based on the config
        const providerNames = [
          "azureActiveDirectory", // From staticwebapp.config.json
          "aad",
          "microsoft",
          "azuread",
        ];

        // Try each provider name until one works
        for (const providerName of providerNames) {
          try {
            // Test if this provider endpoint exists
            const testResponse = await fetch(`/.auth/login/${providerName}`, {
              method: "HEAD",
            });

            if (testResponse.status !== 404) {
              window.location.href = `/.auth/login/${providerName}`;
              return;
            }
          } catch (e) {
            // Continue to next provider
            continue;
          }
        }

        // If all providers fail, show error message
        alert(
          "Unable to access authentication system.\n\n" +
            "The Azure Static Web Apps authentication may not be properly configured.\n" +
            "Please contact support or try again later.",
        );
      } catch (error) {
        console.error("Error determining auth provider:", error);
        alert(
          "Authentication system error.\n\n" +
            "Please check your internet connection and try again.\n" +
            "If the problem persists, contact support.",
        );
      }
    }
  };

  const logout = () => {
    // Check if we're in a production Azure Static Web Apps environment
    if (
      window.location.hostname &&
      (window.location.hostname.includes("azurestaticapps.net") ||
        process.env.NODE_ENV === "production")
    ) {
      // Clear local state first
      setUser(null);
      setGuestSession(null);
      setToken(null);
      localStorage.removeItem("sutra_guest_session_id");
      localStorage.removeItem("vite_local_auth_mode");
      // Then redirect to Azure AD logout
      window.location.href = "/.auth/logout";
    } else {
      // Development mode: clear demo user and guest session
      setUser(null);
      setGuestSession(null);
      setToken(null);
      localStorage.removeItem("sutra_guest_session_id");
      localStorage.removeItem("vite_local_auth_mode");
    }
  };

  const value: AuthContextType = {
    user,
    guestSession,
    isAuthenticated,
    isGuest,
    isLoading,
    login,
    loginAsGuest,
    logout,
    isAdmin,
    token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
