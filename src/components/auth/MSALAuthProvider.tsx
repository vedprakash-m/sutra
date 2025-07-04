/**
 * LEGACY COMPATIBILITY LAYER
 * This file re-exports UnifiedAuthProvider for backward compatibility
 * TODO: Remove this file once all imports are updated to UnifiedAuthProvider
 */

// Re-export everything from UnifiedAuthProvider
export { AuthProvider, useAuth } from "./UnifiedAuthProvider";

// This is a temporary compatibility shim
// All components should eventually import directly from UnifiedAuthProvider
