import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { BarChart3, Clock, Activity, Shield } from 'lucide-react'

import { getApiBase } from '../utils/config'
import { apiFetch } from '../utils/api'

const API_BASE = getApiBase()

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#22C55E',
}

const PIE_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

interface SummaryData {
  period: string
  total_incidents: number
  period_incidents: number
  category_breakdown: Record<string, number>
  type_breakdown: Record<string, number>
  avg_response_time_minutes: number
  judge_decisions_period: number
  agent_health_distribution: Record<string, number>
  agent_breakdown: Record<string, number>
  swarm_breakdown: Record<string, number>
}

interface TrendData {
  period: string
  granularity: string
  incident_trends: Array<{ date: string; count: number }>
  decision_trends: Array<{ date: string; count: number }>
  severity_trends: Array<{ date: string; critical?: number; high?: number; medium?: number; low?: number }>
}

export default function AnalyticsPage() {
  const chartGrid = '#E5E7EB'
  const chartAxis = '#6B7280'
  const chartTooltipBg = '#FFFFFF'
  const chartTooltipBorder = '#E5E7EB'
  const chartLabel = '#111827'

  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [trends, setTrends] = useState<TrendData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [period, setPeriod] = useState('7d')

  useEffect(() => {
    loadAnalytics()
  }, [period])

  const loadAnalytics = async () => {
    setLoading(true)
    setError(false)
    try {
      const [sumRes, trendRes] = await Promise.all([
        apiFetch(`${API_BASE}/dashboard/analytics/summary?period=${period}`),
        apiFetch(`${API_BASE}/dashboard/analytics/trends?period=${period}&granularity=daily`),
      ])
      if (sumRes.ok) {
        setSummary((await sumRes.json()).data || null)
      } else {
        setError(true)
      }
      if (trendRes.ok) {
        setTrends((await trendRes.json()).data || null)
      } else {
        setError(true)
      }
    } catch {
      setError(true)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Analytics
          </h1>
          <div className="h-8 w-32 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card p-4">
              <div className="h-8 w-16 bg-gray-200 rounded animate-pulse mb-2" />
              <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-4 h-80"><div className="h-full w-full bg-gray-200 rounded animate-pulse" /></div>
          <div className="card p-4 h-80"><div className="h-full w-full bg-gray-200 rounded animate-pulse" /></div>
        </div>
      </div>
    )
  }

  const categoryData = summary
    ? Object.entries(summary.category_breakdown).map(([name, value]) => ({ name, value }))
    : []

  const healthData = summary
    ? Object.entries(summary.agent_health_distribution).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: value || 0,
      }))
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-blue-600" />
          Analytics
        </h1>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white"
        >
          <option value="1h">Last Hour</option>
          <option value="6h">Last 6 Hours</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <span className="text-sm text-red-700">Some analytics data failed to load</span>
          <button
            onClick={loadAnalytics}
            className="text-sm text-red-700 font-medium hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-blue-500" />
            <div>
              <p className="text-2xl font-bold text-gray-900">{summary?.period_incidents || 0}</p>
              <p className="text-xs text-gray-500">Incidents ({period})</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-green-500" />
            <div>
              <p className="text-2xl font-bold text-gray-900">{summary?.judge_decisions_period || 0}</p>
              <p className="text-xs text-gray-500">Judge Decisions</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-orange-500" />
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.avg_response_time_minutes?.toFixed(1) || '0.0'}
              </p>
              <p className="text-xs text-gray-500">Avg Response (min)</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-5 h-5 text-purple-500" />
            <div>
              <p className="text-2xl font-bold text-gray-900">{summary?.total_incidents || 0}</p>
              <p className="text-xs text-gray-500">Total Incidents</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Incident Trends */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Incidents Over Time</h3>
          {(trends?.incident_trends || []).length === 0 ? (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No incident trend data for this period</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trends?.incident_trends || []}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartGrid} />
                <XAxis dataKey="date" tick={{ fontSize: 12, fill: chartAxis }} />
                <YAxis tick={{ fontSize: 12, fill: chartAxis }} />
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Incidents"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Category Breakdown */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Category Breakdown</h3>
          {categoryData.length === 0 ? (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No category data for this period</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) =>
                    `${name}: ${isNaN(percent) ? '0' : (percent * 100).toFixed(0)}%`
                  }
                >
                  {categoryData.map((_, index) => (
                    <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Trends */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Severity Trends</h3>
          {(trends?.severity_trends || []).length === 0 ? (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No severity trend data for this period</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={trends?.severity_trends || []}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartGrid} />
                <XAxis dataKey="date" tick={{ fontSize: 12, fill: chartAxis }} />
                <YAxis tick={{ fontSize: 12, fill: chartAxis }} />
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
                <Legend wrapperStyle={{ color: chartLabel }} />
                <Bar dataKey="critical" stackId="a" fill={SEVERITY_COLORS.critical} />
                <Bar dataKey="high" stackId="a" fill={SEVERITY_COLORS.high} />
                <Bar dataKey="medium" stackId="a" fill={SEVERITY_COLORS.medium} />
                <Bar dataKey="low" stackId="a" fill={SEVERITY_COLORS.low} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Agent Health Distribution */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Agent Health Distribution</h3>
          {healthData.length === 0 ? (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No agent health data for this period</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={healthData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke={chartGrid} />
                <XAxis type="number" tick={{ fontSize: 12, fill: chartAxis }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fill: chartAxis }} width={80} />
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
                <Bar dataKey="value" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Charts Row 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Decision Trends */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Judge Decisions Over Time</h3>
          {(trends?.decision_trends || []).length === 0 ? (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No decision trend data for this period</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trends?.decision_trends || []}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartGrid} />
                <XAxis dataKey="date" tick={{ fontSize: 12, fill: chartAxis }} />
                <YAxis tick={{ fontSize: 12, fill: chartAxis }} />
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Decisions"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Type Breakdown */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Incident Type Breakdown</h3>
          {(summary?.type_breakdown && Object.keys(summary.type_breakdown).length > 0) ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart
                data={Object.entries(summary.type_breakdown).map(([name, value]) => ({ name, value }))}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" stroke={chartGrid} />
                <XAxis type="number" tick={{ fontSize: 12, fill: chartAxis }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fill: chartAxis }} width={120} />
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
                <Bar dataKey="value" fill="#10B981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No type data for this period</div>
          )}
        </div>
      </div>

      {/* Charts Row 4 — Agent / Swarm Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Incidents by Agent */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Incidents by Agent</h3>
          {(summary?.agent_breakdown && Object.keys(summary.agent_breakdown).length > 0) ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart
                data={Object.entries(summary.agent_breakdown).map(([name, value]) => ({ name, value }))}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" stroke={chartGrid} />
                <XAxis type="number" tick={{ fontSize: 12, fill: chartAxis }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fill: chartAxis }} width={120} />
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
                <Bar dataKey="value" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No agent data for this period</div>
          )}
        </div>

        {/* Incidents by Swarm */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Incidents by Swarm</h3>
          {(summary?.swarm_breakdown && Object.keys(summary.swarm_breakdown).length > 0) ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={Object.entries(summary.swarm_breakdown).map(([name, value]) => ({ name, value }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) =>
                    `${name}: ${isNaN(percent) ? '0' : (percent * 100).toFixed(0)}%`
                  }
                >
                  {Object.entries(summary.swarm_breakdown).map((_, index) => (
                    <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: chartTooltipBg, borderColor: chartTooltipBorder }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">No swarm data for this period</div>
          )}
        </div>
      </div>
    </div>
  )
}
