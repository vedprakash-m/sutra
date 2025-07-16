import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "react-query";
import React, { useEffect, Suspense } from "react";
import { AuthProvider, useAuth } from "@/components/auth/UnifiedAuthProvider";
import { apiService } from "@/services/api";
import { performanceMonitor } from "@/utils/performance-monitor";
import LoginPage from "@/components/auth/LoginPage";
import NavBar from "@/components/layout/NavBar";

// Lazy load major components for better performance
const Dashboard = React.lazy(() => import("@/components/dashboard/Dashboard"));
const PromptBuilder = React.lazy(
  () => import("@/components/prompt/PromptBuilder"),
);
const CollectionsPage = React.lazy(
  () => import("@/components/collections/CollectionsPage"),
);
const PlaybookBuilder = React.lazy(
  () => import("@/components/playbooks/PlaybookBuilder"),
);
const PlaybookRunner = React.lazy(
  () => import("@/components/playbooks/PlaybookRunner"),
);
const IntegrationsPage = React.lazy(
  () => import("@/components/integrations/IntegrationsPage"),
);
const AdminPanel = React.lazy(() => import("@/components/admin/AdminPanel"));
const ForgePage = React.lazy(() => import("@/components/forge/ForgePage"));
const AnalyticsPage = React.lazy(
  () => import("@/components/analytics/AnalyticsPage"),
);

const queryClient = new QueryClient();

// Loading component for lazy-loaded pages
const PageLoader: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading page...</p>
    </div>
  </div>
);

function AppContent() {
  const { isAuthenticated, isLoading, getAccessToken } = useAuth();

  // Initialize API service with auth token provider
  useEffect(() => {
    // Initialize performance monitoring
    console.log("🔍 Initializing performance monitoring");

    // Track page navigation
    performanceMonitor.trackUserAction("app_load", performance.now(), {
      path: window.location.pathname,
      userAgent: navigator.userAgent,
    });

    // Set up API service token provider
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
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/prompts/new" element={<PromptBuilder />} />
            <Route path="/prompts/:id" element={<PromptBuilder />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/playbooks/new" element={<PlaybookBuilder />} />
            <Route path="/playbooks/:id" element={<PlaybookBuilder />} />
            <Route path="/playbooks/:id/run" element={<PlaybookRunner />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/admin" element={<AdminPanel />} />
            <Route path="/forge" element={<ForgePage />} />
            <Route path="/forge/:projectId" element={<ForgePage />} />
          </Routes>
        </Suspense>
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
