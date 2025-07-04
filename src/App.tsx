import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "react-query";
import { useEffect } from "react";
import { AuthProvider, useAuth } from "@/components/auth/UnifiedAuthProvider";
import { apiService } from "@/services/api";
import LoginPage from "@/components/auth/LoginPage";
import NavBar from "@/components/layout/NavBar";
import Dashboard from "@/components/dashboard/Dashboard";
import PromptBuilder from "@/components/prompt/PromptBuilder";
import CollectionsPage from "@/components/collections/CollectionsPage";
import PlaybookBuilder from "@/components/playbooks/PlaybookBuilder";
import PlaybookRunner from "@/components/playbooks/PlaybookRunner";
import IntegrationsPage from "@/components/integrations/IntegrationsPage";
import AdminPanel from "@/components/admin/AdminPanel";

const queryClient = new QueryClient();

function AppContent() {
  const { isAuthenticated, isLoading, getAccessToken } = useAuth();

  // Initialize API service with auth token provider
  useEffect(() => {
    if (isAuthenticated && getAccessToken) {
      console.log("🔗 Connecting API service to MSAL auth provider");
      apiService.setTokenProvider({
        getAccessToken: async () => {
          try {
            const token = await getAccessToken();
            console.log("🔑 API service got token:", token ? "✓" : "✗");
            return token;
          } catch (error) {
            console.error("❌ Error getting token for API service:", error);
            return null;
          }
        },
      });
    } else {
      // Clear token provider when not authenticated
      apiService.setTokenProvider(null);
    }
  }, [isAuthenticated, getAccessToken]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div
            data-testid="loading-spinner"
            className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"
          ></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/prompts/new" element={<PromptBuilder />} />
          <Route path="/prompts/:id" element={<PromptBuilder />} />
          <Route path="/collections" element={<CollectionsPage />} />
          <Route path="/playbooks/new" element={<PlaybookBuilder />} />
          <Route path="/playbooks/:id" element={<PlaybookBuilder />} />
          <Route path="/playbooks/:id/run" element={<PlaybookRunner />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <AppContent />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

// For testing purposes - component without Router
export function AppWithoutRouter() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
