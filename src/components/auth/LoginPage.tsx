import { useState } from "react";
import { useAuth } from "./AuthProvider";

export default function LoginPage() {
  const { login } = useAuth();
  const [selectedRole, setSelectedRole] = useState<"user" | "admin">("user");

  // Check if we're in development mode
  const isDevelopment =
    process.env.NODE_ENV === "development" ||
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";

  const handleLogin = () => {
    if (isDevelopment) {
      // Store role preference for development mode only
      localStorage.setItem("sutra_demo_role", selectedRole);
    }
    login();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome to Sutra
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Multi-LLM Prompt Studio for AI Operations
          </p>
          <p className="mt-1 text-xs text-gray-500">
            Beta Version - Secure Azure AD Authentication
          </p>
        </div>

        <div className="mt-8 space-y-6">
          <div className="bg-white py-8 px-6 shadow rounded-lg">
            <div className="text-center space-y-4">
              <div className="mx-auto h-12 w-12 text-indigo-600">
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>

              <h3 className="text-lg font-medium text-gray-900">
                Secure Authentication Required
              </h3>

              <p className="text-sm text-gray-600">
                {isDevelopment
                  ? "Development Mode: Sign in with demo credentials or Microsoft account"
                  : "Sign in with your Microsoft account to access the Sutra platform"}
              </p>

              {/* Development Mode Role Selection - Only show in development */}
              {isDevelopment && (
                <div className="space-y-3">
                  <p className="text-xs text-gray-500">
                    Development Mode - Select Role:
                  </p>
                  <div className="flex space-x-4 justify-center">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="role"
                        value="user"
                        checked={selectedRole === "user"}
                        onChange={(e) =>
                          setSelectedRole(e.target.value as "user" | "admin")
                        }
                        className="mr-2"
                      />
                      <span className="text-sm">Regular User</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="role"
                        value="admin"
                        checked={selectedRole === "admin"}
                        onChange={(e) =>
                          setSelectedRole(e.target.value as "user" | "admin")
                        }
                        className="mr-2"
                      />
                      <span className="text-sm">Admin User</span>
                    </label>
                  </div>
                </div>
              )}

              <button
                onClick={handleLogin}
                className="w-full flex justify-center items-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 0C5.383 0 0 5.383 0 12s5.383 12 12 12 12-5.383 12-12S18.617 0 12 0zm5.5 16.5h-11v-1h11v1zm0-2h-11v-1h11v1zm0-2h-11v-1h11v1zm0-2h-11v-1h11v1z" />
                </svg>
                {isDevelopment
                  ? "Sign in (Development Mode)"
                  : "Sign in with Microsoft"}
              </button>
            </div>
          </div>

          <div className="text-center">
            <div className="text-xs text-gray-500 space-y-1">
              <p>🔒 Your data is protected with enterprise-grade security</p>
              <p>🚀 Beta testing program - help us improve Sutra</p>
              <p>📧 Questions? Contact support for assistance</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
