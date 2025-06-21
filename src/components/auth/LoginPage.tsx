import { useState } from "react";
import { useAuth } from "./AuthProvider";

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const [loginType, setLoginType] = useState<"user" | "admin">("user");

  const handleLogin = async () => {
    try {
      await login(
        loginType === "admin" ? "admin@sutra.ai" : "user@sutra.ai",
        loginType === "admin",
      );
    } catch (error) {
      console.error("Login failed:", error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Sutra
          </h2>
          <p className="text-gray-600 mb-8">
            Multi-LLM Prompt Studio - Development Mode
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Login as:
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    className="mr-2"
                    checked={loginType === "user"}
                    onChange={() => setLoginType("user")}
                  />
                  Regular User
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    className="mr-2"
                    checked={loginType === "admin"}
                    onChange={() => setLoginType("admin")}
                  />
                  Administrator
                </label>
              </div>
            </div>
          </div>

          <div>
            <button
              onClick={handleLogin}
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isLoading ? "Signing in..." : "Sign in (Development Mode)"}
            </button>
          </div>

          <div className="text-xs text-gray-500 text-center">
            This is a development environment. In production, this would
            integrate with Azure AD B2C.
          </div>
        </div>
      </div>
    </div>
  );
}
