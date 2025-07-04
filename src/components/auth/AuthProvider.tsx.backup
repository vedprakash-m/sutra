import {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
} from "react";
import { VedUser, GuestSession } from "@/types/auth";

interface AuthContextType {
  user: VedUser | null;
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
  const [user, setUser] = useState<VedUser | null>(null);
  const [guestSession, setGuestSession] = useState<GuestSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  const isAuthenticated =
    !!user && user.vedProfile?.subscriptionTier !== "guest";
  const isGuest = user?.vedProfile?.subscriptionTier === "guest";
  const isAdmin =
    user?.permissions?.includes("admin") ||
    user?.permissions?.includes("Administrator") ||
    false;

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

            // Use standardized user extraction function
            const authUser = extractStandardUser(principal);

            // Check backend for role confirmation if user has standard role
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
                    // Update permissions if backend confirms admin role
                    authUser.permissions = [...authUser.permissions, "admin"];
                    authUser.vedProfile.subscriptionTier = "enterprise";
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
        const guestUser: VedUser = {
          id: data.session.id,
          email: "guest@sutra.app",
          name: "Guest User",
          givenName: "Guest",
          familyName: "User",
          permissions: [],
          vedProfile: {
            profileId: data.session.id,
            subscriptionTier: "guest",
            appsEnrolled: ["sutra"],
            preferences: {},
          },
        };

        const guestSessionData: GuestSession = {
          id: data.session.id,
          usage: data.usage || {},
          limits: data.limits || {},
          remaining: data.remaining || {},
          active: data.session.active,
          createdAt: new Date().toISOString(),
          expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
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

/**
 * Standardized user extraction function - Apps_Auth_Requirement.md compliance
 * Creates VedUser object from Azure Static Web Apps or MSAL token claims
 */
function extractStandardUser(principal: any): VedUser {
  // Validate required claims
  if (!principal.userId || !principal.userDetails) {
    throw new Error("Invalid principal: missing required claims");
  }

  const email = principal.userDetails;
  const userId = principal.userId;

  // Extract name from claims or derive from email
  let name = principal.claims?.find(
    (c: any) =>
      c.typ === "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
  )?.val;

  let givenName =
    principal.claims?.find(
      (c: any) =>
        c.typ ===
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
    )?.val || "";

  let familyName =
    principal.claims?.find(
      (c: any) =>
        c.typ ===
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
    )?.val || "";

  // If no name claim, derive from givenName and familyName
  if (!name) {
    name = `${givenName} ${familyName}`.trim();
  }

  // If still no name, extract from email
  if (!name && email) {
    const emailName = email.split("@")[0];
    name = emailName
      .split(/[._-]/)
      .map(
        (part: string) =>
          part.charAt(0).toUpperCase() + part.slice(1).toLowerCase(),
      )
      .join(" ");
  }

  // Final fallback
  if (!name) {
    name = email || "User";
  }

  // Extract permissions from roles
  const permissions = principal.userRoles || [];

  // Determine subscription tier based on roles and email
  let subscriptionTier: "free" | "premium" | "enterprise" | "guest" = "free";
  if (email === "vedprakash.m@outlook.com") {
    subscriptionTier = "enterprise";
  }

  return {
    id: userId,
    email: email,
    name: name.trim(),
    givenName: givenName,
    familyName: familyName,
    permissions: permissions,
    vedProfile: {
      profileId: userId,
      subscriptionTier: subscriptionTier,
      appsEnrolled: ["sutra"],
      preferences: {},
    },
  };
}
