import {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
} from "react";
import {
  useMsal,
  MsalProvider,
  AuthenticatedTemplate,
  UnauthenticatedTemplate,
} from "@azure/msal-react";
import { AccountInfo, EventType, EventMessage } from "@azure/msal-browser";
import {
  msalInstance,
  loginRequest,
  silentRequest,
  getAuthMode,
} from "@/config/authConfig";
import {
  VedUser,
  GuestSession,
  AuthContextType,
  EntraIdClaims,
} from "@/types/auth";

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Custom hook to use auth context
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

/**
 * Internal Auth Provider Component (uses MSAL hooks)
 */
function AuthProviderInternal({ children }: AuthProviderProps) {
  const { instance, accounts } = useMsal();
  const [user, setUser] = useState<VedUser | null>(null);
  const [guestSession, setGuestSession] = useState<GuestSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [authMode] = useState(() => getAuthMode());

  const isAuthenticated =
    !!user && user.vedProfile.subscriptionTier !== "guest";
  const isGuest = user?.vedProfile.subscriptionTier === "guest";
  const isAdmin = user?.permissions.includes("admin") || false;

  /**
   * Extract VedUser from MSAL account
   */
  const createVedUserFromAccount = async (
    account: AccountInfo,
  ): Promise<VedUser> => {
    try {
      // Get ID token claims
      const idTokenClaims = account.idTokenClaims as unknown as EntraIdClaims;

      // Determine user role
      let userRole: "user" | "admin" = "user";

      // Check for admin role in token claims
      if (
        idTokenClaims?.roles?.includes("admin") ||
        idTokenClaims?.app_roles?.includes("admin")
      ) {
        userRole = "admin";
      }

      // Override for specific admin users
      if (account.username === "vedprakash.m@outlook.com") {
        userRole = "admin";
      }

      // Try to get role from backend API
      try {
        const accessToken = await getAccessTokenSilent();
        if (accessToken) {
          const roleResponse = await fetch("/api/getroles", {
            headers: {
              Authorization: `Bearer ${accessToken}`,
              "Content-Type": "application/json",
            },
          });

          if (roleResponse.ok) {
            const roleData = await roleResponse.json();
            if (roleData.roles?.includes("admin")) {
              userRole = "admin";
            }
          }
        }
      } catch (error) {
        console.warn("Could not fetch user role from backend:", error);
      }

      const vedUser: VedUser = {
        id: account.localAccountId || account.homeAccountId,
        email: account.username,
        name: account.name || idTokenClaims?.name || account.username,
        givenName: idTokenClaims?.given_name || "",
        familyName: idTokenClaims?.family_name || "",
        permissions: userRole === "admin" ? ["admin", "user"] : ["user"],
        vedProfile: {
          profileId: account.localAccountId || account.homeAccountId,
          subscriptionTier: userRole === "admin" ? "enterprise" : "free",
          appsEnrolled: ["sutra"],
          preferences: {},
        },
      };

      return vedUser;
    } catch (error) {
      console.error("Error creating VedUser from account:", error);
      throw error;
    }
  };

  /**
   * Get access token silently
   */
  const getAccessTokenSilent = async (): Promise<string | null> => {
    try {
      if (accounts.length === 0) {
        return null;
      }

      const request = {
        ...silentRequest,
        account: accounts[0],
      };

      const response = await instance.acquireTokenSilent(request);
      return response.accessToken;
    } catch (error) {
      console.warn("Silent token acquisition failed:", error);
      return null;
    }
  };

  /**
   * Initialize authentication state
   */
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsLoading(true);

        if (authMode === "msal") {
          // MSAL authentication mode
          if (accounts.length > 0) {
            const account = accounts[0];
            const vedUser = await createVedUserFromAccount(account);
            const accessToken = await getAccessTokenSilent();

            setUser(vedUser);
            setToken(accessToken);
            console.log("✅ MSAL authentication initialized:", vedUser);
          } else {
            console.log("ℹ️ No MSAL accounts found");
          }
        } else if (authMode === "swa") {
          // Fallback to Azure Static Web Apps authentication
          await initializeSwaAuth();
        } else {
          // Mock authentication for local development
          await initializeMockAuth();
        }
      } catch (error) {
        console.error("Auth initialization failed:", error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [accounts, authMode, instance]);

  /**
   * Initialize Azure Static Web Apps authentication (fallback)
   */
  const initializeSwaAuth = async () => {
    try {
      const response = await fetch("/.auth/me");
      if (response.ok) {
        const authInfo = await response.json();
        if (authInfo.clientPrincipal) {
          const principal = authInfo.clientPrincipal;

          let userRole: "user" | "admin" = "user";
          if (
            principal.userRoles?.includes("admin") ||
            principal.userDetails === "vedprakash.m@outlook.com"
          ) {
            userRole = "admin";
          }

          const vedUser: VedUser = {
            id: principal.userId,
            email: principal.userDetails,
            name: principal.userDetails.split("@")[0],
            givenName: principal.userDetails.split("@")[0],
            familyName: "",
            permissions: userRole === "admin" ? ["admin", "user"] : ["user"],
            vedProfile: {
              profileId: principal.userId,
              subscriptionTier: userRole === "admin" ? "enterprise" : "free",
              appsEnrolled: ["sutra"],
              preferences: {},
            },
          };

          setUser(vedUser);
          setToken("swa-token");
          console.log("✅ SWA authentication initialized:", vedUser);
        }
      }
    } catch (error) {
      console.warn("SWA auth initialization failed:", error);
    }
  };

  /**
   * Initialize mock authentication (local development)
   */
  const initializeMockAuth = async () => {
    try {
      const response = await fetch("/.auth/me");
      if (response.ok) {
        const authInfo = await response.json();
        if (authInfo.clientPrincipal) {
          const principal = authInfo.clientPrincipal;

          const vedUser: VedUser = {
            id: principal.userId || "mock-user-123",
            email: principal.userDetails || "dev@example.com",
            name: "Local Developer",
            givenName: "Local",
            familyName: "Developer",
            permissions: ["admin", "user"], // Default to admin for local development
            vedProfile: {
              profileId: principal.userId || "mock-user-123",
              subscriptionTier: "enterprise",
              appsEnrolled: ["sutra"],
              preferences: {},
            },
          };

          setUser(vedUser);
          setToken("mock-token");
          console.log("✅ Mock authentication initialized:", vedUser);
        }
      }
    } catch (error) {
      console.warn("Mock auth initialization failed:", error);
    }
  };

  /**
   * Login function
   */
  const login = async (): Promise<void> => {
    try {
      if (authMode === "msal") {
        await instance.loginPopup(loginRequest);
        // User state will be updated by the useEffect hook
      } else {
        // Redirect to Azure Static Web Apps login
        window.location.href = "/.auth/login/aad";
      }
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  };

  /**
   * Guest login function
   */
  const loginAsGuest = async (): Promise<void> => {
    try {
      const guestUser: VedUser = {
        id: `guest-${Date.now()}`,
        email: "",
        name: "Guest User",
        givenName: "Guest",
        familyName: "User",
        permissions: [],
        vedProfile: {
          profileId: `guest-${Date.now()}`,
          subscriptionTier: "guest",
          appsEnrolled: ["sutra"],
          preferences: {},
        },
      };

      const session: GuestSession = {
        id: `session-${Date.now()}`,
        usage: {},
        limits: { llm_calls: 5 },
        remaining: { llm_calls: 5 },
        active: true,
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
      };

      setUser(guestUser);
      setGuestSession(session);
      setToken("guest-token");
      console.log("✅ Guest session created:", { guestUser, session });
    } catch (error) {
      console.error("Guest login failed:", error);
      throw error;
    }
  };

  /**
   * Logout function
   */
  const logout = (): void => {
    try {
      if (authMode === "msal") {
        instance.logoutPopup();
      } else {
        window.location.href = "/.auth/logout";
      }

      setUser(null);
      setGuestSession(null);
      setToken(null);
      console.log("✅ Logout completed");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  /**
   * Get access token for API calls
   */
  const getAccessToken = async (): Promise<string | null> => {
    if (authMode === "msal") {
      return await getAccessTokenSilent();
    }
    return token;
  };

  /**
   * Refresh authentication state
   */
  const refreshAuth = async (): Promise<void> => {
    if (authMode === "msal" && accounts.length > 0) {
      try {
        const vedUser = await createVedUserFromAccount(accounts[0]);
        const accessToken = await getAccessTokenSilent();

        setUser(vedUser);
        setToken(accessToken);
        console.log("✅ Auth state refreshed");
      } catch (error) {
        console.error("Auth refresh failed:", error);
      }
    }
  };

  const contextValue: AuthContextType = {
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
    getAccessToken,
    refreshAuth,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}

/**
 * Main Auth Provider Component (wraps MSAL Provider)
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const authMode = getAuthMode();

  // Set up MSAL event handling
  useEffect(() => {
    const callbackId = msalInstance.addEventCallback((event: EventMessage) => {
      if (event.eventType === EventType.LOGIN_SUCCESS) {
        console.log("✅ MSAL login success:", event.payload);
      } else if (event.eventType === EventType.LOGIN_FAILURE) {
        console.error("❌ MSAL login failure:", event.payload);
      }
    });

    return () => {
      if (callbackId) {
        msalInstance.removeEventCallback(callbackId);
      }
    };
  }, []);

  if (authMode === "msal") {
    return (
      <MsalProvider instance={msalInstance}>
        <AuthProviderInternal>{children}</AuthProviderInternal>
      </MsalProvider>
    );
  } else {
    // For SWA and mock modes, use the internal provider directly
    return <AuthProviderInternal>{children}</AuthProviderInternal>;
  }
}

// Export components for conditional rendering
export { AuthenticatedTemplate, UnauthenticatedTemplate };
