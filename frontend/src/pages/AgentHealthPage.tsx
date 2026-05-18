import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  CheckCircle,
  XCircle,
  MinusCircle,
  Search,
  Eye,
  ChevronDown,
  ChevronUp,
  FolderOpen,
} from 'lucide-react'
import { getApiBase } from '../utils/config'
import { apiFetch } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'

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
  category: string
  last_seen: string
  created_at: string
  updated_at: string
}

const CATEGORY_ORDER = [
  'Swarm Agents',
  'Production Agents',
  'Playground Agents',
  'Demo Agents',
  'DPI Proxy',
  'System',
]

function categorySortKey(cat: string): number {
  const idx = CATEGORY_ORDER.indexOf(cat)
  return idx === -1 ? 999 : idx
}

function categoryBadgeColor(cat: string): string {
  switch (cat) {
    case 'Swarm Agents':
      return 'bg-purple-100 text-purple-700'
    case 'Production Agents':
      return 'bg-blue-100 text-blue-700'
    case 'Playground Agents':
      return 'bg-orange-100 text-orange-700'
    case 'Demo Agents':
      return 'bg-gray-100 text-gray-600'
    case 'DPI Proxy':
      return 'bg-cyan-100 text-cyan-700'
    case 'System':
      return 'bg-slate-100 text-slate-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

export default function AgentHealthPage() {
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())
  const { messages } = useWebSocket()

  const fetchAgents = (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true)
    apiFetch(`${API_BASE}/agents`)
      .then((r) => (r.ok ? r.json() : null))
      .then((res) => {
        if (res?.data?.items) {
          const items: Agent[] = res.data.items
          setAgents(items)
          // Auto-expand categories that have online/healthy agents
          const autoExpand = new Set<string>()
          items.forEach((a) => {
            if (a.status === 'online' || a.status === 'healthy') {
              autoExpand.add(a.category || 'Production Agents')
            }
          })
          // If nothing to auto-expand, expand Swarm and Production
          if (autoExpand.size === 0) {
            autoExpand.add('Swarm Agents')
            autoExpand.add('Production Agents')
          }
          setExpandedCategories((prev) => {
            const next = new Set(prev)
            autoExpand.forEach((c) => next.add(c))
            return next
          })
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchAgents()
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      fetchAgents({ silent: true })
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (messages.length === 0) return
    const latest = messages[0]
    if (latest.event_type === 'agent_status_updated') {
      fetchAgents({ silent: true })
    }
  }, [messages])

  const filtered = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.system_id.toLowerCase().includes(search.toLowerCase())
  )

  // Group by category
  const grouped: Record<string, Agent[]> = {}
  filtered.forEach((a) => {
    const cat = a.category || 'Production Agents'
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(a)
  })

  const sortedCategories = Object.keys(grouped).sort(
    (a, b) => categorySortKey(a) - categorySortKey(b)
  )

  const toggleCategory = (cat: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(cat)) {
        next.delete(cat)
      } else {
        next.add(cat)
      }
      return next
    })
  }

  const expandAll = () => {
    setExpandedCategories(new Set(sortedCategories))
  }

  const collapseAll = () => {
    setExpandedCategories(new Set())
  }

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
        <div className="flex items-center gap-2">
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
          <button
            onClick={expandAll}
            className="text-xs font-medium text-blue-600 hover:text-blue-700 px-2 py-1 rounded hover:bg-blue-50"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="text-xs font-medium text-gray-600 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-50"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <SummaryCard
          title="Total Agents"
          value={agents.length}
          icon={<Activity className="w-5 h-5" />}
          color="bg-blue-50 text-blue-700"
        />
        <SummaryCard
          title="Healthy"
          value={agents.filter((a) => a.status === 'healthy' || a.status === 'online').length}
          icon={<CheckCircle className="w-5 h-5" />}
          color="bg-green-50 text-green-700"
        />
        <SummaryCard
          title="Degraded"
          value={agents.filter((a) => a.status === 'degraded').length}
          icon={<MinusCircle className="w-5 h-5" />}
          color="bg-yellow-50 text-yellow-700"
        />
        <SummaryCard
          title="Critical"
          value={agents.filter((a) => a.status === 'critical').length}
          icon={<XCircle className="w-5 h-5" />}
          color="bg-red-50 text-red-700"
        />
        <SummaryCard
          title="Offline"
          value={agents.filter((a) => a.status === 'offline').length}
          icon={<XCircle className="w-5 h-5" />}
          color="bg-gray-100 text-gray-600"
        />
      </div>

      {/* Category Accordion */}
      <div className="space-y-3">
        {sortedCategories.map((cat) => {
          const isExpanded = expandedCategories.has(cat)
          const catAgents = grouped[cat]
          const onlineCount = catAgents.filter((a) => a.status === 'online' || a.status === 'healthy').length

          return (
            <div key={cat} className="card overflow-hidden">
              {/* Accordion Header */}
              <button
                onClick={() => toggleCategory(cat)}
                className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FolderOpen className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-semibold text-gray-900">{cat}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${categoryBadgeColor(cat)}`}>
                    {catAgents.length}
                  </span>
                  {onlineCount > 0 && (
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      {onlineCount} online
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </div>
              </button>

              {/* Accordion Content */}
              {isExpanded && (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-white border-b border-gray-100">
                      <tr>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Agent
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Health
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Lie Rate
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Incidents
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Bypasses
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Decision Rate
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Actions
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Status
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-2">
                          Last Seen
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {catAgents.map((agent) => (
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
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                navigate(`/incidents?agent_id=${encodeURIComponent(agent.system_id)}`)
                              }}
                              className="text-sm text-blue-600 hover:text-blue-700 font-medium hover:underline"
                            >
                              {agent.incident_count}
                            </button>
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
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                navigate(`/incidents?agent_id=${encodeURIComponent(agent.system_id)}`)
                              }}
                              className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100"
                              title="View incidents for this agent"
                            >
                              <Eye className="w-3 h-3" /> View
                            </button>
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-medium ${
                                agent.status === 'healthy' || agent.status === 'online'
                                  ? 'bg-green-100 text-green-700'
                                  : agent.status === 'degraded'
                                  ? 'bg-yellow-100 text-yellow-700'
                                  : agent.status === 'offline'
                                  ? 'bg-gray-100 text-gray-600'
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
                </div>
              )}
            </div>
          )
        })}

        {filtered.length === 0 && (
          <div className="card p-8 text-center text-gray-500">
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
