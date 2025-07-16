// Stub implementation for TypeScript compilation
export const useAuth = () => {
  return {
    user: { role: "user" } as any,
    isAuthenticated: false,
    login: () => {},
    logout: () => {},
  };
};
