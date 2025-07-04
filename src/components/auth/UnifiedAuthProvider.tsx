import {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
} from "react";
import { useMsal, MsalProvider } from "@azure/msal-react";
import { AccountInfo, PublicClientApplication } from "@azure/msal-browser";
import {
  getMSALConfig,
  getLoginRequestConfig,
  getSilentTokenRequestConfig,
  validateConfig,
} from "@/config";
import { VedUser, AuthContextType, EntraIdClaims } from "@/types/auth";

// Initialize MSAL with consolidated configuration
const msalConfig = getMSALConfig();
const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL
const ensureMsalInitialized = async (): Promise<void> => {
  if (!msalInstance.getActiveAccount()) {
    await msalInstance.initialize();
  }
};

// Validate configuration on module load
if (!validateConfig()) {
  console.error("Configuration validation failed");
}

// Initialize MSAL on module load
ensureMsalInitialized().catch(console.error);

// Request configurations
const loginRequest = getLoginRequestConfig();
const silentRequest = getSilentTokenRequestConfig();

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
 * Internal Auth Provider Component - Unified MSAL Only
 * This eliminates the dual authentication paradigm for consistency
 */
function AuthProviderInternal({ children }: AuthProviderProps) {
  const { instance, accounts } = useMsal();
  const [user, setUser] = useState<VedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  const isAuthenticated =
    !!user && user.vedProfile.subscriptionTier !== "guest";
  const isGuest = user?.vedProfile.subscriptionTier === "guest";
  const isAdmin = user?.permissions.includes("admin") || false;

  /**
   * Extract VedUser from MSAL account - Apps_Auth_Requirement.md Compliant
   */
  const createVedUserFromAccount = async (
    account: AccountInfo,
  ): Promise<VedUser> => {
    try {
      const idTokenClaims = account.idTokenClaims as unknown as EntraIdClaims;

      // Validate required claims
      if (!account.localAccountId && !account.homeAccountId) {
        throw new Error("Invalid token: missing required user identifier");
      }

      if (!account.username) {
        throw new Error("Invalid token: missing required email claim");
      }

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

        // Ensure MSAL is initialized
        await ensureMsalInitialized();

        // Wait for any redirect handling
        await new Promise((resolve) => setTimeout(resolve, 100));

        // Check for existing accounts
        const currentAccounts = instance.getAllAccounts();
        console.log("🔍 Current accounts found:", currentAccounts.length);

        if (currentAccounts.length > 0) {
          const account = currentAccounts[0];
          console.log("🔑 Using existing account:", account.username);

          try {
            const vedUser = await createVedUserFromAccount(account);
            const accessToken = await getAccessTokenSilent();

            setUser(vedUser);
            setToken(accessToken);
            console.log("✅ Authentication successful:", vedUser.email);
          } catch (error) {
            console.error("❌ Error processing account:", error);
            setUser(null);
            setToken(null);
          }
        } else {
          console.log("ℹ️ No accounts found");

          // For local development, create a mock authenticated user
          if (window.location.hostname === "localhost") {
            console.log(
              "🔧 Local development: creating mock authenticated user",
            );

            const mockUser: VedUser = {
              id: "admin-user-local-dev",
              email: "vedprakash.m@outlook.com",
              name: "Ved Prakash Mishra",
              givenName: "Ved Prakash",
              familyName: "Mishra",
              permissions: ["admin", "user"],
              vedProfile: {
                profileId: "admin-user-local-dev",
                subscriptionTier: "enterprise",
                appsEnrolled: ["sutra"],
                preferences: {},
              },
            };

            setUser(mockUser);
            setToken("mock-access-token-local-dev");
            console.log(
              "✅ Mock authentication successful for local development",
            );
          } else {
            setUser(null);
            setToken(null);
          }
        }

        setIsLoading(false);
      } catch (error) {
        console.error("❌ Auth initialization error:", error);
        setUser(null);
        setToken(null);
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [instance]);

  /**
   * Login function
   */
  const login = async (): Promise<void> => {
    try {
      console.log("🔐 Initiating MSAL login...");
      await instance.loginRedirect({
        ...loginRequest,
        scopes: [...loginRequest.scopes], // Convert readonly to mutable
      });
    } catch (error) {
      console.error("❌ Login failed:", error);
      throw error;
    }
  };

  /**
   * Logout function
   */
  const logout = async (): Promise<void> => {
    try {
      console.log("🚪 Logging out...");
      await instance.logoutRedirect({
        postLogoutRedirectUri: window.location.origin,
      });
    } catch (error) {
      console.error("❌ Logout failed:", error);
      throw error;
    }
  };

  /**
   * Get access token
   */
  const getAccessToken = async (): Promise<string | null> => {
    try {
      if (!token) {
        const newToken = await getAccessTokenSilent();
        if (newToken) {
          setToken(newToken);
          return newToken;
        }
      }
      return token;
    } catch (error) {
      console.error("❌ Error getting access token:", error);
      return null;
    }
  };

  const authContextValue: AuthContextType = {
    user,
    isAuthenticated,
    isGuest,
    isAdmin,
    isLoading,
    login,
    logout,
    getAccessToken,
    guestSession: null, // Not implemented in this unified version
    loginAsGuest: async () => {}, // Not implemented in this unified version
    token,
    refreshAuth: async () => {}, // Not implemented in this unified version
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Main Auth Provider Component
 */
export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <MsalProvider instance={msalInstance}>
      <AuthProviderInternal>{children}</AuthProviderInternal>
    </MsalProvider>
  );
}

export default {
  AuthProvider,
  useAuth,
};
