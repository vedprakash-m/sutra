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
  roles: string[];
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email?: string, isAdmin?: boolean) => Promise<void>;
  logout: () => Promise<void>;
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

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  const isAuthenticated = !!user;
  const isAdmin = user?.roles.includes("admin") ?? false;

  // Initialize auth state from localStorage
  useEffect(() => {
    const savedUser = localStorage.getItem("sutra_user");
    const savedToken = localStorage.getItem("sutra_token");

    if (savedUser && savedToken) {
      setUser(JSON.parse(savedUser));
      setToken(savedToken);
    }
    setIsLoading(false);
  }, []);

  const login = async (email = "user@sutra.ai", isAdminUser = false) => {
    setIsLoading(true);
    try {
      // Development mode authentication
      const mockUser: User = {
        id: isAdminUser ? "mock-admin-id" : "mock-user-id",
        email: isAdminUser ? "admin@sutra.ai" : email,
        name: isAdminUser ? "Development Admin" : "Development User",
        roles: isAdminUser ? ["admin", "user"] : ["user"],
      };

      const mockToken = isAdminUser ? "mock-admin-token" : "mock-token";

      setUser(mockUser);
      setToken(mockToken);

      // Save to localStorage
      localStorage.setItem("sutra_user", JSON.stringify(mockUser));
      localStorage.setItem("sutra_token", mockToken);
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("sutra_user");
    localStorage.removeItem("sutra_token");
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
