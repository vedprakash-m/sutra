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
  login: () => void;
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

          if (authInfo.clientPrincipal) {
            const principal = authInfo.clientPrincipal;

            // Extract user information from claims
            const email =
              principal.claims.find(
                (c) =>
                  c.typ ===
                  "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
              )?.val || principal.userDetails;
            const name =
              principal.claims.find(
                (c) =>
                  c.typ ===
                  "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
              )?.val || email;

            // Determine user role from Azure AD roles
            const userRole = principal.userRoles?.includes("admin")
              ? "admin"
              : "user";

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
          }
        }

        // Fallback: Check localStorage for demo user (don't auto-create)
        const storedUser = localStorage.getItem("sutra_demo_user");
        if (storedUser) {
          const demoUser = JSON.parse(storedUser);
          setUser(demoUser);
          setToken("demo-token");
        }
        // If no stored user, user remains null and will see login page
      } catch (error) {
        console.error("Failed to check auth status:", error);
        // On error, user remains null and will see login page
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = () => {
    // Try Static Web Apps login first
    if (
      window.location.hostname &&
      window.location.hostname.includes("azurestaticapps.net")
    ) {
      window.location.href = "/.auth/login/aad";
    } else {
      // Fallback: simulate login for demo based on localStorage preference
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
    }
  };

  const logout = () => {
    // Try Static Web Apps logout first
    if (
      window.location.hostname &&
      window.location.hostname.includes("azurestaticapps.net")
    ) {
      // Clear local state first
      setUser(null);
      setToken(null);
      localStorage.removeItem("sutra_demo_user");
      // Then redirect to logout
      window.location.href = "/.auth/logout";
    } else {
      // Fallback: clear demo user
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
