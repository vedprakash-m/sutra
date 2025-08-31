/**
 * Canonical AuthProvider - Single Source of Truth
 *
 * This is the canonical authentication provider export that all components
 * and tests should use. It provides a clean, consistent interface while
 * internally using the UnifiedAuthProvider implementation.
 */

// Re-export the AuthProvider as the canonical provider
export { AuthProvider } from "./UnifiedAuthProvider";
export { useAuth } from "./UnifiedAuthProvider";

// Re-export all auth-related types and interfaces from types
export type {
  AuthContextType,
  SutraUser,
  GuestSession,
  EntraIdClaims,
} from "@/types/auth";

// Default export for convenience
export { AuthProvider as default } from "./UnifiedAuthProvider";
