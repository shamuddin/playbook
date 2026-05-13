import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  Shield,
  Activity,
  Gavel,
  BookOpen,
  TrendingUp,
  TrendingDown,
  Server,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface DashboardData {
  overview: {
    total_incidents: number
    open_incidents: number
    resolved_incidents: number
    critical_alerts: number
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
  }
  judge_layer: {
    total_decisions: number
    bypasses_detected: number
    avg_latency_ms: number
    allow_rate: number
    deny_rate: number
  }
  playbooks: {
    total: number
    active: number
    success_rate: number
  }
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/dashboard`)
      .then((r) => r.json())
      .then((res) => {
        setData(res.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

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
        <span className="text-sm text-gray-500">
          {new Date().toLocaleDateString()}
        </span>
      </div>

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
