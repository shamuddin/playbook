import { useEffect, useState, useCallback } from 'react'
import {
  Shield,
  Eye,
  Filter,
  X,
  CheckCircle,
  AlertTriangle,
  Ban,
  Activity,
  Clock,
} from 'lucide-react'
import { apiFetch } from '../utils/api'

const API_BASE = (window as any).__API_BASE__ || '/api/v1'

interface DpiEntry {
  request_id: string
  timestamp: string
  direction: string
  action: string
  matched_rule: string
  metadata: Record<string, any>
  mismatches: string[]
}

interface DpiStats {
  total_intercepted: number
  blocked: number
  allowed: number
  quarantined: number
  top_rules: { rule: string; count: number }[]
  avg_risk_score: number
}

function getVerdictColor(verdict: string) {
  const v = (verdict || '').toUpperCase()
  if (v === 'BLOCK' || v === 'DENY') return 'bg-red-100 text-red-700 border-red-200'
  if (v === 'QUARANTINE') return 'bg-orange-100 text-orange-700 border-orange-200'
  if (v === 'ALLOW') return 'bg-green-100 text-green-700 border-green-200'
  return 'bg-gray-100 text-gray-700 border-gray-200'
}

function getVerdictIcon(verdict: string) {
  const v = (verdict || '').toUpperCase()
  if (v === 'BLOCK' || v === 'DENY') return <Ban className="w-4 h-4" />
  if (v === 'QUARANTINE') return <AlertTriangle className="w-4 h-4" />
  if (v === 'ALLOW') return <CheckCircle className="w-4 h-4" />
  return <Activity className="w-4 h-4" />
}

function formatTimestamp(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString()
  } catch {
    return ts
  }
}

export default function DpiLiveFeedPage() {
  const [entries, setEntries] = useState<DpiEntry[]>([])
  const [stats, setStats] = useState<DpiStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [verdictFilter, setVerdictFilter] = useState<string>('ALL')

  const fetchData = useCallback(async () => {
    try {
      const logsRes = await apiFetch(`${API_BASE}/integrations/lobstertrap/logs?limit=100`)
      const logsData = await logsRes.json()
      if (logsData.success) {
        setEntries(logsData.data.entries || [])
      }
      const statsRes = await apiFetch(`${API_BASE}/integrations/lobstertrap/stats`)
      const statsData = await statsRes.json()
      if (statsData.success) {
        setStats(statsData.data)
      }
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [fetchData])

  const filtered = entries.filter((e) => {
    if (verdictFilter === 'ALL') return true
    return (e.action || '').toUpperCase() === verdictFilter
  })

  const blockRate = stats && stats.total_intercepted > 0
    ? Math.round((stats.blocked / stats.total_intercepted) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Eye className="w-7 h-7 text-blue-600" />
            DPI Live Feed
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time deep prompt inspection via{' '}
            <span className="font-semibold text-blue-600">Veea Lobster Trap</span>
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
          <Shield className="w-4 h-4" />
          Powered by Veea Lobster Trap
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-sm text-gray-500">Total Intercepted</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {stats?.total_intercepted ?? 0}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-500">Blocked</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {stats?.blocked ?? 0}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-500">Allowed</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {stats?.allowed ?? 0}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-500">Block Rate</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{blockRate}%</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <Filter className="w-4 h-4 text-gray-400" />
        <div className="flex gap-2">
          {['ALL', 'ALLOW', 'BLOCK', 'QUARANTINE'].map((v) => (
            <button
              key={v}
              onClick={() => setVerdictFilter(v)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                verdictFilter === v
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {v === 'ALL' ? 'All Verdicts' : v}
            </button>
          ))}
        </div>
        {verdictFilter !== 'ALL' && (
          <button
            onClick={() => setVerdictFilter('ALL')}
            className="text-sm text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Feed Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Time</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Prompt</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Verdict</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Matched Rule</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Risk</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Detected</th>
              </tr>
            </thead>
            <tbody>
              {loading && entries.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-3" />
                    Loading DPI feed...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400">
                    No DPI events match the selected filter.
                  </td>
                </tr>
              ) : (
                filtered.map((entry, idx) => {
                  const meta = entry.metadata || {}
                  const detected = meta.detected || {}
                  const riskScore = meta.risk_score || 0
                  const prompt = meta.prompt || meta.content || JSON.stringify(meta).slice(0, 80)

                  return (
                    <tr
                      key={entry.request_id || idx}
                      className="border-b border-gray-50 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-4 whitespace-nowrap text-gray-500">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTimestamp(entry.timestamp)}
                        </div>
                      </td>
                      <td className="py-3 px-4 max-w-xs">
                        <div className="truncate text-gray-800" title={prompt}>
                          {prompt || '—'}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getVerdictColor(
                            entry.action
                          )}`}
                        >
                          {getVerdictIcon(entry.action)}
                          {entry.action || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-700 font-medium">
                        {entry.matched_rule || '—'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                riskScore > 70
                                  ? 'bg-red-500'
                                  : riskScore > 40
                                  ? 'bg-orange-500'
                                  : 'bg-green-500'
                              }`}
                              style={{ width: `${Math.min(riskScore, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">{riskScore}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(detected)
                            .filter(([, v]) => v === true || v === 'true')
                            .slice(0, 3)
                            .map(([k]) => (
                              <span
                                key={k}
                                className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full"
                              >
                                {k}
                              </span>
                            ))}
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
