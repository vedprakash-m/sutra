/**
 * Sutra User - Email-based authentication with Microsoft Entra ID default tenant
 *
 * This interface supports simplified authentication using any Microsoft account
 * with email as the primary identifier and automatic user registration.
 */

export interface SutraUser {
  /** Email address serves as primary identifier */
  id: string; // Email address

  /** Primary email address from Entra ID */
  email: string;

  /** Full display name from Entra ID profile */
  name: string;

  /** Microsoft Entra ID tenant ID */
  tenantId?: string;

  /** Microsoft Entra ID object ID */
  objectId?: string;

  /** User role in Sutra application */
  role: "user" | "admin";

  /** User preferences */
  preferences: {
    defaultLLM: string;
    theme: string;
    notifications: boolean;
    [key: string]: any;
  };

  /** Usage statistics */
  usage: {
    totalPrompts: number;
    totalCollections: number;
    totalPlaybooks: number;
    totalForgeProjects: number;
  };

  /** Account creation timestamp */
  createdAt: string;

  /** Last activity timestamp */
  lastActive: string;

  /** Account active status */
  isActive: boolean;
}

/**
 * Guest session for anonymous users
 */
export interface GuestSession {
  /** Unique session identifier */
  id: string;

  /** Usage tracking by service/action */
  usage: Record<string, number>;

  /** Rate limits by service/action */
  limits: Record<string, number>;

  /** Remaining quota by service/action */
  remaining: Record<string, number>;

  /** Session active status */
  /** Session active status */
  active: boolean;

  /** Session creation timestamp */
  createdAt: string;

  /** Session expiration timestamp */
  expiresAt: string;

  /** IP address for rate limiting */
  ipAddress?: string;

  /** Geographic location for analytics */
  location?: {
    country?: string;
    region?: string;
    city?: string;
  };
}

/**
 * Authentication context interface
 */
export interface AuthContextType {
  /** Current authenticated user or null */
  user: SutraUser | null;

  /** Current guest session or null */
  guestSession: GuestSession | null;

  /** Whether user is authenticated */
  isAuthenticated: boolean;

  /** Whether current session is guest/anonymous */
  isGuest: boolean;

  /** Whether authentication state is being determined */
  isLoading: boolean;

  /** Initiate login flow */
  login: () => Promise<void>;

  /** Start anonymous/guest session */
  loginAsGuest: () => Promise<void>;

  /** Logout and clear session */
  logout: () => void;

  /** Whether user has admin privileges */
  isAdmin: boolean;

  /** Current authentication token */
  token: string | null;

  /** Get access token for API calls */
  getAccessToken: () => Promise<string | null>;

  /** Refresh authentication state */
  refreshAuth: () => Promise<void>;
}

/**
 * Microsoft Entra ID token claims
 */
export interface EntraIdClaims {
  /** Audience */
  aud: string;

  /** Issuer */
  iss: string;

  /** Issued at time */
  iat: number;

  /** Not before time */
  nbf: number;

  /** Expiration time */
  exp: number;

  /** Subject (user ID) */
  sub: string;

  /** Object ID */
  oid: string;

  /** Tenant ID */
  tid: string;

  /** Unique name */
  unique_name: string;

  /** User Principal Name */
  upn: string;

  /** Name */
  name: string;

  /** Given name */
  given_name?: string;

  /** Family name */
  family_name?: string;

  /** Email */
  email?: string;

  /** Roles */
  roles?: string[];

  /** Application roles */
  app_roles?: string[];
}
