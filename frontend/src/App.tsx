import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './components/AuthProvider'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import IncidentsPage from './pages/IncidentsPage'
import IncidentDetailPage from './pages/IncidentDetailPage'
import JudgePage from './pages/JudgePage'
import AgentHealthPage from './pages/AgentHealthPage'
import CompliancePage from './pages/CompliancePage'
import PolicyBuilderPage from './pages/PolicyBuilderPage'
import ReviewQueuePage from './pages/ReviewQueuePage'
import SettingsPage from './pages/SettingsPage'
import ForensicsPage from './pages/ForensicsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import PlaygroundPage from './pages/PlaygroundPage'
import AgentSwarmPage from './pages/AgentSwarmPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="incidents" element={<IncidentsPage />} />
        <Route path="incidents/:id" element={<IncidentDetailPage />} />
        <Route path="judge" element={<JudgePage />} />
        <Route path="agents" element={<AgentHealthPage />} />
        <Route path="compliance" element={<CompliancePage />} />
        <Route path="policy-builder" element={<PolicyBuilderPage />} />
        <Route path="review" element={<ReviewQueuePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="forensics/:id" element={<ForensicsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="playground" element={<PlaygroundPage />} />
        <Route path="swarm" element={<AgentSwarmPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
