import { BrowserRouter, Routes, Route } from 'react-router-dom'
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

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
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
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
