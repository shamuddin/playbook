import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { AlertTriangle, Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react'
import { getApiBase, getPageSize } from '../utils/config'
import { apiFetch } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'

const API_BASE = getApiBase()

const INCIDENT_TYPE_NAMES: Record<string, string> = {
  'AGT-DEL-001': 'Data Destruction',
  'AGT-FIN-002': 'Unauthorized Financial',
  'AGT-PER-003': 'Permission Escalation',
  'AGT-HRM-004': 'Harmful Output',
  'AGT-EXT-005': 'Data Exfiltration',
  'AGT-INJ-006': 'Prompt Injection',
  'AGT-HAL-007': 'Hallucination Cascade',
  'AGT-CRE-008': 'Credential Exposure',
  'AGT-RAT-009': 'Rate Limit Abuse',
  'AGT-DRF-010': 'Model Drift',
  'AGT-TLM-011': 'Tool Misuse',
  'AGT-GAP-012': 'Coverage Gap',
  'AGT-SPY-013': 'Systematic Espionage',
  'AGT-BYP-014': 'Guardrail Bypass',
  'AGT-PRV-015': 'Privacy Violation',
  'AGT-REG-016': 'Regulatory Trigger',
  'AGT-POL-017': 'Organization Policy Switching',
}

function getIncidentName(code: string): string {
  return INCIDENT_TYPE_NAMES[code] || code
}

interface AgentOption {
  system_id: string
  name: string
}

interface Incident {
  id: string
  incident_id: string
  incident_type: string
  severity: string
  status: string
  event_id: string | null
  agent_id: string | null
  swarm_id: string | null
  confidence: number
  judge_verdict: string | null
  bypass_detected: boolean
  created_at: string
}

export default function IncidentsPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(() => getPageSize())
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [agentFilter, setAgentFilter] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search)
    return urlParams.get('agent_id') || ''
  })
  const [swarmFilter, setSwarmFilter] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search)
    return urlParams.get('swarm_id') || ''
  })
  const [agents, setAgents] = useState<AgentOption[]>([])
  const [livePulse, setLivePulse] = useState(false)
  const { messages } = useWebSocket()

  const fetchAgents = useCallback(async () => {
    try {
      const res = await apiFetch(`${API_BASE}/agents?page_size=100`)
      if (res.ok) {
        const data = await res.json()
        const items = (data.data?.items || []).map((a: any) => ({
          system_id: a.system_id,
          name: a.name,
        }))
        setAgents(items)
      }
    } catch {
      // ignore
    }
  }, [])

  const fetchIncidents = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true)
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', String(pageSize))
    if (statusFilter) params.set('status', statusFilter)
    if (severityFilter) params.set('severity', severityFilter)
    if (agentFilter) params.set('agent_id', agentFilter)
    if (swarmFilter) params.set('swarm_id', swarmFilter)
    if (search) params.set('q', search)

    try {
      const res = await apiFetch(`${API_BASE}/incidents?${params.toString()}`)
      if (!res.ok) throw new Error('Unauthorized')
      const data = await res.json()
      setIncidents(data.data || [])
      setTotal(data.total || 0)
    } catch {
      setIncidents([])
      setTotal(0)
    }
    setLoading(false)
  }, [page, pageSize, statusFilter, severityFilter, agentFilter, swarmFilter, search])

  useEffect(() => {
    fetchAgents()
  }, [fetchAgents])

  useEffect(() => {
    fetchIncidents()
  }, [fetchIncidents])

  // Sync agentFilter from URL query param (deep-linked from Agent Health)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const urlAgent = urlParams.get('agent_id')
    if (urlAgent && urlAgent !== agentFilter) {
      setAgentFilter(urlAgent)
      setPage(1)
    }
  }, [location.search])

  useEffect(() => {
    const latest = messages[0]
    if (latest && latest.event_type === 'incident_detected') {
      fetchIncidents({ silent: true })
      setLivePulse(true)
      const t = setTimeout(() => setLivePulse(false), 3000)
      return () => clearTimeout(t)
    }
  }, [messages, fetchIncidents])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchIncidents()
  }

  const severityBadge = (severity: string) => {
    const map: Record<string, string> = {
      critical: 'bg-red-100 text-red-700',
      high: 'bg-orange-100 text-orange-700',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-green-100 text-green-700',
    }
    return map[severity] || 'bg-gray-100 text-gray-700'
  }

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      new: 'bg-blue-100 text-blue-700',
      detected: 'bg-purple-100 text-purple-700',
      responding: 'bg-amber-100 text-amber-700',
      resolved: 'bg-green-100 text-green-700',
      escalated: 'bg-red-100 text-red-700',
    }
    return map[status] || 'bg-gray-100 text-gray-700'
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Incidents</h1>
          {livePulse && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 animate-pulse">
              New incident
            </span>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Incident ID, type, agent..."
                className="w-full pl-9 pr-3 py-2 border border-gray-200 bg-white text-gray-900 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-gray-200 bg-white text-gray-900 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="new">New</option>
              <option value="detected">Detected</option>
              <option value="responding">Responding</option>
              <option value="resolved">Resolved</option>
              <option value="escalated">Escalated</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Severity</label>
            <select
              value={severityFilter}
              onChange={(e) => { setSeverityFilter(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-gray-200 bg-white text-gray-900 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Agent</label>
            <select
              value={agentFilter}
              onChange={(e) => { setAgentFilter(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-gray-200 bg-white text-gray-900 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Agents</option>
              {agents.map((a) => (
                <option key={a.system_id} value={a.system_id}>{a.name || a.system_id}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Swarm</label>
            <input
              type="text"
              value={swarmFilter}
              onChange={(e) => { setSwarmFilter(e.target.value); setPage(1) }}
              placeholder="Swarm ID..."
              className="px-3 py-2 border border-gray-200 bg-white text-gray-900 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button type="submit" className="btn-primary py-2 px-4">
            <Filter className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : incidents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No incidents found</div>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">ID</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Severity</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Agent</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Swarm</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Confidence</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Judge</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {incidents.map((inc) => (
                  <tr
                    key={inc.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/incidents/${inc.incident_id}`)}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-600">{inc.incident_id}</td>
                    <td className="px-4 py-3 text-gray-900">
                      <div className="font-medium">{getIncidentName(inc.incident_type)}</div>
                      <div className="text-xs text-gray-500 font-mono">{inc.incident_type}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityBadge(inc.severity)}`}>
                        {inc.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusBadge(inc.status)}`}>
                        {inc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {inc.agent_id ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/agents`)
                          }}
                          className="text-blue-600 hover:text-blue-700 hover:underline"
                          title={inc.agent_id}
                        >
                          {agents.find((a) => a.system_id === inc.agent_id)?.name || inc.agent_id}
                        </button>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{inc.swarm_id || '—'}</td>
                    <td className="px-4 py-3 text-gray-600">{(inc.confidence * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {inc.bypass_detected && (
                          <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                        )}
                        {inc.judge_verdict ? (
                          <span className={`text-xs font-medium ${
                            inc.judge_verdict === 'ALLOW' ? 'text-green-600' :
                            inc.judge_verdict === 'DENY' ? 'text-red-600' :
                            inc.judge_verdict === 'QUARANTINE' ? 'text-orange-600' :
                            'text-purple-600'
                          }`}>
                            {inc.judge_verdict}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(inc.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
              <span className="text-xs text-gray-500">
                Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} of {total}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs text-gray-600">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
