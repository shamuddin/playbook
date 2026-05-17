import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Shield,
  Activity,
  Gavel,
  BookOpen,
  TrendingUp,
  TrendingDown,
  Server,
  Radio,
  Zap,
  Clock,
  FileText,
  Eye,
  Swords,
  ChevronRight,
} from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'
import { getApiBase, getRefreshInterval } from '../utils/config'
import { apiFetch } from '../utils/api'

const API_BASE = getApiBase()

interface DashboardData {
  overview: {
    total_incidents: number
    open_incidents: number
    resolved_incidents: number
    critical_alerts: number
    avg_resolution_time_minutes?: number
  }
  incidents: {
    by_severity: Record<string, number>
    by_status: Record<string, number>
    trend: { direction: string; change_percent: number }
  }
  agents: {
    total: number
    online: number
    degraded: number
    offline: number
    avg_health_score: number
    agents_with_incidents?: number
  }
  judge_layer: {
    total_decisions: number
    bypasses_detected: number
    avg_latency_ms: number
    allow_rate: number
    deny_rate: number
    quarantine_rate?: number
    escalate_rate?: number
    top_bypass_pattern?: {
      id: string
      name: string
      detection_count: number
    } | null
    agents_under_judge_watch?: number
  }
  playbooks: {
    total: number
    active: number
    success_rate: number
    most_used?: {
      id: string
      name: string
      executions_24h: number
    } | null
  }
  lobstertrap?: {
    running: boolean
    recent_events: number
  }
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [ltRunning, setLtRunning] = useState(false)
  const [ltEvents, setLtEvents] = useState(0)
  const [attacking, setAttacking] = useState(false)
  const [swarmRunning, setSwarmRunning] = useState(false)
  const { connected, messages } = useWebSocket()

  const fetchDashboard = useCallback(() => {
    apiFetch(`${API_BASE}/dashboard`)
      .then((r) => (r.ok ? r.json() : null))
      .then((res) => {
        if (res?.data) setData(res.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const launchAttack = useCallback(async () => {
    setAttacking(true)
    try {
      const res = await apiFetch(`${API_BASE}/demo/attack`, { method: 'POST' })
      if (!res.ok) throw new Error('Attack request failed')
      // Dashboard will auto-update via WebSocket incident_detected events
    } catch {
      alert('Failed to launch attack. Is the backend running?')
    } finally {
      setAttacking(false)
    }
  }, [])

  const fetchLtQuickStatus = useCallback(() => {
    apiFetch(`${API_BASE}/integrations/lobstertrap/status`)
      .then((r) => (r.ok ? r.json() : null))
      .then((res) => {
        if (res?.data) {
          setLtRunning(res.data.running)
        }
      })
      .catch(() => {})
    apiFetch(`${API_BASE}/integrations/lobstertrap/logs?limit=1`)
      .then((r) => (r.ok ? r.json() : null))
      .then((res) => {
        if (res?.data?.total !== undefined) {
          setLtEvents(res.data.total)
        }
      })
      .catch(() => {})
  }, [])

  const fetchSwarmStatus = useCallback(() => {
    apiFetch(`${API_BASE}/playground/sessions`)
      .then((r) => (r.ok ? r.json() : null))
      .then((res) => {
        if (res?.data?.items) {
          const running = res.data.items.some((s: any) => s.status === 'running')
          setSwarmRunning(running)
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    fetchDashboard()
    fetchLtQuickStatus()
    fetchSwarmStatus()
    const intervalSeconds = getRefreshInterval()
    if (intervalSeconds > 0) {
      const id = setInterval(() => {
        fetchDashboard()
        fetchLtQuickStatus()
        fetchSwarmStatus()
      }, intervalSeconds * 1000)
      return () => clearInterval(id)
    }
  }, [fetchDashboard, fetchLtQuickStatus, fetchSwarmStatus])

  useEffect(() => {
    if (messages.length === 0) return
    const msg = messages[0]
    if (!msg) return

    setData((prev) => {
      if (!prev) return prev
      const next: DashboardData = { ...prev }

      // Incident detected
      if (msg.event_type === 'incident_detected') {
        next.overview = { ...next.overview, total_incidents: next.overview.total_incidents + 1 }
        if (msg.severity === 'critical') {
          next.overview = { ...next.overview, critical_alerts: next.overview.critical_alerts + 1 }
        }
        next.incidents = { ...next.incidents, by_severity: { ...next.incidents.by_severity } }
        const sev = msg.severity || 'unknown'
        next.incidents.by_severity[sev] = (next.incidents.by_severity[sev] || 0) + 1
      }

      // Agent status updated — re-fetch dashboard to keep counts accurate
      if (msg.event_type === 'agent_status_updated') {
        fetchDashboard()
      }

      // Judge decision
      if (msg.event_type === 'judge_decision') {
        next.judge_layer = { ...next.judge_layer, total_decisions: next.judge_layer.total_decisions + 1 }
      }

      // Playground incident created
      if (msg.type === 'playground_event' && msg.event_type === 'incident_created') {
        next.overview = { ...next.overview, total_incidents: next.overview.total_incidents + 1 }
        if (msg.severity === 'critical') {
          next.overview = { ...next.overview, critical_alerts: next.overview.critical_alerts + 1 }
        }
        next.incidents = { ...next.incidents, by_severity: { ...next.incidents.by_severity } }
        const sev = msg.severity || 'unknown'
        next.incidents.by_severity[sev] = (next.incidents.by_severity[sev] || 0) + 1
      }

      return next
    })
  }, [messages])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="card p-8 text-center">
        <p className="text-gray-500">Failed to load dashboard data.</p>
      </div>
    )
  }

  const severityColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-700',
    high: 'bg-orange-100 text-orange-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-green-100 text-green-700',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={launchAttack}
            disabled={attacking}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white text-sm font-semibold rounded-lg shadow transition-colors"
          >
            <Swords className="w-4 h-4" />
            {attacking ? 'Firing...' : 'Launch Attack'}
          </button>
          <span className="text-sm text-gray-500">
            {new Date().toLocaleDateString()}
          </span>
        </div>
      </div>

      {swarmRunning && (
        <div className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
          <span className="text-sm font-semibold text-red-700">
            LIVE — Agent Swarm is running. Real-time incidents being captured.
          </span>
          <button
            onClick={() => navigate('/playground')}
            className="ml-auto text-xs font-medium text-red-700 hover:text-red-800 underline"
          >
            View Playground
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Incidents"
          value={data.overview.total_incidents}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="bg-blue-50 text-blue-700"
          trend={data.incidents.trend}
        />
        <KpiCard
          title="Critical Alerts"
          value={data.overview.critical_alerts}
          icon={<Shield className="w-5 h-5" />}
          color="bg-red-50 text-red-700"
        />
        <KpiCard
          title="Agent Health"
          value={`${data.agents.avg_health_score}%`}
          icon={<Activity className="w-5 h-5" />}
          color="bg-green-50 text-green-700"
        />
        <KpiCard
          title="Judge Decisions"
          value={data.judge_layer.total_decisions}
          icon={<Gavel className="w-5 h-5" />}
          color="bg-purple-50 text-purple-700"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incidents by Severity */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Incidents by Severity
          </h3>
          <div className="space-y-3">
            {Object.entries(data.incidents.by_severity).map(([sev, count]) => (
              <div key={sev} className="flex items-center gap-3">
                <span
                  className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                    severityColors[sev] || 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {sev}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      sev === 'critical'
                        ? 'bg-red-500'
                        : sev === 'high'
                        ? 'bg-orange-500'
                        : sev === 'medium'
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    style={{
                      width: `${Math.min(
                        (count /
                          Math.max(
                            ...Object.values(data.incidents.by_severity)
                          )) *
                          100,
                        100
                      )}%`,
                    }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-8 text-right">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Status */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Agent Fleet Status
          </h3>
          <div className="space-y-4">
            <StatusRow label="Online" value={data.agents.online} color="bg-green-500" />
            <StatusRow label="Degraded" value={data.agents.degraded} color="bg-yellow-500" />
            <StatusRow label="Offline" value={data.agents.offline} color="bg-red-500" />
            <div className="pt-2 border-t border-gray-100">
              <span className="text-sm text-gray-500">
                Total agents: {data.agents.total}
              </span>
            </div>
          </div>
        </div>

        {/* Judge Layer Stats */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Judge Layer Performance
          </h3>
          <div className="space-y-3">
            <MetricRow label="Allow Rate" value={`${(data.judge_layer.allow_rate * 100).toFixed(1)}%`} />
            <MetricRow label="Deny Rate" value={`${(data.judge_layer.deny_rate * 100).toFixed(1)}%`} />
            <MetricRow label="Bypasses Detected" value={data.judge_layer.bypasses_detected} />
            <MetricRow label="Avg Latency" value={`${data.judge_layer.avg_latency_ms.toFixed(1)} ms`} />
          </div>
        </div>
      </div>

      {/* Playbooks & Compliance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Playbooks
          </h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="text-2xl font-bold text-gray-900">
                {data.playbooks.active}/{data.playbooks.total}
              </div>
              <p className="text-sm text-gray-500">Active playbooks</p>
              {data.playbooks.most_used && (
                <p className="text-xs text-gray-400 mt-1">
                  Most used: <span className="font-medium text-gray-600">{data.playbooks.most_used.name}</span> ({data.playbooks.most_used.executions_24h})
                </p>
              )}
            </div>
            <div className="flex-1">
              <div className="text-2xl font-bold text-gray-900">
                {(data.playbooks.success_rate * 100).toFixed(0)}%
              </div>
              <p className="text-sm text-gray-500">Success rate</p>
            </div>
            <BookOpen className="w-10 h-10 text-blue-200" />
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            System Status
          </h3>
          <div className="flex items-center gap-3">
            <Server className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-700">API Healthy</span>
            <span className="ml-auto px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
              Operational
            </span>
          </div>
        </div>

        <div className="card border-l-4 border-blue-500">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Eye className="w-4 h-4 text-blue-500" />
            Lobster Trap DPI
            <span className="ml-auto px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full font-medium">
              Powered by Veea
            </span>
          </h3>
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-3 h-3 rounded-full ${ltRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-700">
              {ltRunning ? 'Proxy Running' : 'Proxy Stopped'}
            </span>
          </div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-500">Recent DPI events</span>
            <span className="text-sm font-medium text-gray-900">{ltEvents}</span>
          </div>
          <button
            onClick={() => navigate('/dpi-live')}
            className="w-full mt-1 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 px-3 py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            View DPI Live Feed
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Judge Watch & Bypass Patterns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Gavel className="w-4 h-4 text-purple-500" />
            Agents Under Judge Watch
          </h3>
          <div className="flex items-center gap-4">
            <div className="text-3xl font-bold text-gray-900">
              {data.judge_layer.agents_under_judge_watch || 0}
            </div>
            <div className="text-sm text-gray-500">
              agents with judge decisions tracked
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            Top Bypass Pattern
          </h3>
          {data.judge_layer.top_bypass_pattern ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">
                  {data.judge_layer.top_bypass_pattern.name}
                </span>
                <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full">
                  {data.judge_layer.top_bypass_pattern.detection_count} detections
                </span>
              </div>
              <div className="text-xs text-gray-500 font-mono">
                {data.judge_layer.top_bypass_pattern.id}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No bypass patterns detected</p>
          )}
        </div>
      </div>

      {/* Real-Time Incident Feed */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-500" />
            Live Incident Feed
          </h3>
          <div className="flex items-center gap-2">
            <Radio className={`w-3 h-3 ${connected ? 'text-green-500' : 'text-gray-400'}`} />
            <span className={`text-xs ${connected ? 'text-green-600' : 'text-gray-500'}`}>
              {connected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
        {messages.length === 0 ? (
          <p className="text-sm text-gray-500">Waiting for events...</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {messages.slice(0, 20).map((msg, i) => (
              <div
                key={`${msg.event_id || msg.incident_id || msg.timestamp || ''}-${i}`}
                onClick={() => msg.incident_id && navigate(`/incidents/${msg.incident_id}`)}
                className={`flex items-center gap-3 p-2 rounded-lg text-sm ${
                  msg.incident_id ? 'cursor-pointer hover:bg-gray-50' : ''
                } ${
                  msg.event_type === 'demo_scenario_triggered'
                    ? 'bg-blue-50'
                    : msg.event_type === 'incident_status_updated'
                    ? 'bg-purple-50'
                    : 'bg-gray-50'
                }`}
              >
                {msg.event_type === 'demo_scenario_triggered' ? (
                  <Zap className="w-4 h-4 text-blue-500 shrink-0" />
                ) : msg.event_type === 'incident_status_updated' ? (
                  <Activity className="w-4 h-4 text-purple-500 shrink-0" />
                ) : msg.event_type === 'INCIDENT_CLASSIFIED' ? (
                  <Shield className="w-4 h-4 text-indigo-500 shrink-0" />
                ) : msg.event_type === 'INCIDENT_FORENSICS_COMPLETE' ? (
                  <FileText className="w-4 h-4 text-green-500 shrink-0" />
                ) : msg.event_type === 'HUMAN_REVIEW_REQUIRED' ? (
                  <Gavel className="w-4 h-4 text-orange-500 shrink-0" />
                ) : (
                  <Clock className="w-4 h-4 text-gray-400 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <span className="font-medium text-gray-900">{msg.event_type}</span>
                  {msg.incident_id && (
                    <span className="text-xs text-gray-500 ml-2">{msg.incident_id}</span>
                  )}
                  {msg.agent_id && (
                    <span className="text-xs text-gray-500 ml-2">Agent: {msg.agent_id}</span>
                  )}
                  {msg.swarm_id && (
                    <span className="text-xs text-gray-500 ml-2">Swarm: {msg.swarm_id}</span>
                  )}
                  {msg.severity && (
                    <span className={`ml-2 px-1.5 py-0.5 rounded text-xs font-medium ${
                      msg.severity === 'critical' ? 'bg-red-100 text-red-700' :
                      msg.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                      msg.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {msg.severity}
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-400 shrink-0">
                  {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function KpiCard({
  title,
  value,
  icon,
  color,
  trend,
}: {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
  trend?: { direction: string; change_percent: number }
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className={`p-2 rounded-lg ${color}`}>{icon}</span>
        {trend && (
          <span
            className={`flex items-center gap-1 text-xs font-medium ${
              trend.direction === 'increasing' ? 'text-red-600' : 'text-green-600'
            }`}
          >
            {trend.direction === 'increasing' ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {trend.change_percent}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500">{title}</div>
    </div>
  )
}

function StatusRow({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  return (
    <div className="flex items-center gap-3">
      <div className={`w-3 h-3 rounded-full ${color}`} />
      <span className="text-sm text-gray-600 flex-1">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value}</span>
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value}</span>
    </div>
  )
}
