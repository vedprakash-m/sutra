/**
 * VedUser Standard - Apps_Auth_Requirement.md Compliance
 *
 * This interface ensures 100% compliance with Vedprakash domain authentication requirements
 * and provides unified user data structure across all .vedprakash.net applications.
 */

export interface VedUser {
  /** Unique user identifier from Microsoft Entra ID (primary key) */
  id: string;

  /** Primary email address from Entra ID */
  email: string;

  /** Full display name from Entra ID profile */
  name: string;

  /** User's given name (first name) */
  givenName: string;

  /** User's family name (last name) */
  familyName: string;

  /** App-specific permissions from JWT claims */
  permissions: string[];

  /** Vedprakash domain profile information */
  vedProfile: {
    /** Vedprakash domain profile ID */
    profileId: string;

    /** User's subscription tier (guest for anonymous users) */
    subscriptionTier: "free" | "premium" | "enterprise" | "guest";

    /** List of enrolled Vedprakash apps */
    appsEnrolled: string[];

    /** User preferences across domain */
    preferences: Record<string, any>;
  };
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
  user: VedUser | null;

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
