import { useEffect, useState } from 'react'
import {
  Activity,
  CheckCircle,
  XCircle,
  MinusCircle,
  Search,
} from 'lucide-react'
import { getApiBase } from '../utils/config'

const API_BASE = getApiBase()

interface Agent {
  id: string
  system_id: string
  name: string
  description: string
  health_score: number
  lie_rate: number
  incident_count: number
  bypass_attempt_count: number
  judge_decision_count: number
  judge_decision_rate: number
  suprawall_connected: boolean
  is_active: boolean
  status: string
  last_seen: string
  created_at: string
  updated_at: string
}

export default function AgentHealthPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/agents`)
      .then((r) => r.json())
      .then((res) => {
        setAgents(res.data?.items || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const filtered = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.system_id.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Agent Health</h1>
        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2">
          <Search className="w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search agents..."
            className="outline-none text-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Agents"
          value={agents.length}
          icon={<Activity className="w-5 h-5" />}
          color="bg-blue-50 text-blue-700"
        />
        <SummaryCard
          title="Healthy"
          value={agents.filter((a) => a.health_score >= 80).length}
          icon={<CheckCircle className="w-5 h-5" />}
          color="bg-green-50 text-green-700"
        />
        <SummaryCard
          title="Degraded"
          value={agents.filter((a) => a.health_score >= 50 && a.health_score < 80).length}
          icon={<MinusCircle className="w-5 h-5" />}
          color="bg-yellow-50 text-yellow-700"
        />
        <SummaryCard
          title="Critical"
          value={agents.filter((a) => a.health_score < 50).length}
          icon={<XCircle className="w-5 h-5" />}
          color="bg-red-50 text-red-700"
        />
      </div>

      {/* Agent Table */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Agent
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Health
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Lie Rate
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Incidents
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Bypasses
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Decision Rate
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Status
              </th>
              <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                Last Seen
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((agent) => (
              <tr key={agent.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        agent.health_score >= 80
                          ? 'bg-green-500'
                          : agent.health_score >= 50
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {agent.name}
                      </p>
                      <p className="text-xs text-gray-500">{agent.system_id}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-gray-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          agent.health_score >= 80
                            ? 'bg-green-500'
                            : agent.health_score >= 50
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${agent.health_score}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-700">
                      {agent.health_score}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-700">
                    {(agent.lie_rate * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-700">
                    {agent.incident_count}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-700">
                    {agent.bypass_attempt_count}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-700">
                    {(agent.judge_decision_rate * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      agent.status === 'healthy'
                        ? 'bg-green-100 text-green-700'
                        : agent.status === 'degraded'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {agent.status ? agent.status.charAt(0).toUpperCase() + agent.status.slice(1) : 'Unknown'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-gray-500">
                    {agent.last_seen ? new Date(agent.last_seen).toLocaleDateString() : '—'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No agents found.
          </div>
        )}
      </div>
    </div>
  )
}

function SummaryCard({
  title,
  value,
  icon,
  color,
}: {
  title: string
  value: number
  icon: React.ReactNode
  color: string
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-3">
        <span className={`p-2 rounded-lg ${color}`}>{icon}</span>
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">{title}</div>
        </div>
      </div>
    </div>
  )
}
