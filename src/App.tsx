import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { AuthProvider, useAuth } from '@/components/auth/AuthProvider'
import LoginPage from '@/components/auth/LoginPage'
import NavBar from '@/components/layout/NavBar'
import Dashboard from '@/components/dashboard/Dashboard'
import PromptBuilder from '@/components/prompt/PromptBuilder'
import CollectionsPage from '@/components/collections/CollectionsPage'
import PlaybookBuilder from '@/components/playbooks/PlaybookBuilder'
import PlaybookRunner from '@/components/playbooks/PlaybookRunner'
import IntegrationsPage from '@/components/integrations/IntegrationsPage'
import AdminPanel from '@/components/admin/AdminPanel'

const queryClient = new QueryClient()

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
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
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
