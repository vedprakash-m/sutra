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
  role: string; // Single role: "user" or "admin"
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
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
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  const isAuthenticated = !!user;
  const isAdmin = user?.role === "admin";

  // Initialize auth state from Static Web Apps or fallback
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // First, try Static Web Apps authentication
        const response = await fetch("/.auth/me");

        if (response.ok) {
          const authInfo: StaticWebAppsUser = await response.json();
          console.log("Azure Static Web Apps auth info:", authInfo);

          if (authInfo.clientPrincipal) {
            const principal = authInfo.clientPrincipal;

            // Extract user information from claims
            const email =
              principal.claims.find(
                (c) =>
                  c.typ ===
                  "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
              )?.val || principal.userDetails;
            // Extract name from claims or derive from email
            let name = principal.claims.find(
              (c) =>
                c.typ ===
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
            )?.val;

            // If no name claim, extract name from email
            if (!name && email) {
              // Extract name part from email (before @)
              const emailName = email.split("@")[0];
              // Convert common email formats to display names
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

            // Get user role from our backend role assignment
            // Note: Azure Static Web Apps should call /api/getroles and populate userRoles
            // but we'll also fetch it directly as a fallback
            let userRole = "user";
            if (principal.userRoles?.includes("admin")) {
              userRole = "admin";
            }

            // Fallback: If no roles in userRoles, fetch from our backend
            if (
              !principal.userRoles ||
              principal.userRoles.length === 0 ||
              (principal.userRoles.length === 1 &&
                principal.userRoles[0] === "authenticated")
            ) {
              try {
                const roleResponse = await fetch("/api/getroles", {
                  headers: {
                    "Content-Type": "application/json",
                  },
                });
                if (roleResponse.ok) {
                  const roleData = await roleResponse.json();
                  if (roleData.roles && roleData.roles.includes("admin")) {
                    userRole = "admin";
                  }
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
              role: userRole, // Single role based on Azure AD
            };

            setUser(authUser);
            setToken("static-web-apps-token");
            setIsLoading(false);
            return;
          } else {
            console.log("No clientPrincipal found in auth response");
          }
        } else {
          console.log(
            "Auth endpoint response not ok:",
            response.status,
            response.statusText,
          );
        }

        // Only allow demo mode in development environments
        if (
          process.env.NODE_ENV === "development" ||
          window.location.hostname === "localhost" ||
          window.location.hostname === "127.0.0.1"
        ) {
          // Fallback: Check localStorage for demo user (development only)
          const storedUser = localStorage.getItem("sutra_demo_user");
          if (storedUser) {
            const demoUser = JSON.parse(storedUser);
            setUser(demoUser);
            setToken("demo-token");
          }
        }
        // In production, if no authenticated user, user remains null and will see login page
      } catch (error) {
        console.error("Failed to check auth status:", error);
        // On error, user remains null and will see login page
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async () => {
    // Check if we're in a development environment
    if (
      process.env.NODE_ENV === "development" ||
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1"
    ) {
      // Development mode: use demo authentication
      const storedRole = localStorage.getItem("sutra_demo_role") || "user";
      const demoUser: User = {
        id: storedRole === "admin" ? "demo-admin-001" : "demo-user-001",
        email: storedRole === "admin" ? "admin@sutra.app" : "demo@sutra.app",
        name: storedRole === "admin" ? "Demo Admin" : "Demo User",
        role: storedRole, // Single role, not array
      };

      localStorage.setItem("sutra_demo_user", JSON.stringify(demoUser));
      setUser(demoUser);
      setToken("demo-token");
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
      setToken(null);
      localStorage.removeItem("sutra_demo_user");
      // Then redirect to Azure AD logout
      window.location.href = "/.auth/logout";
    } else {
      // Development mode: clear demo user
      setUser(null);
      setToken(null);
      localStorage.removeItem("sutra_demo_user");
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    isAdmin,
    token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
