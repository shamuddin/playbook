import { useEffect, useState } from 'react'
import {
  Shield,
  AlertTriangle,
  Clock,
  CheckCircle,
  XCircle,
  Ban,
  UserCheck,
  Activity,
  Lock,
} from 'lucide-react'

import { getApiBase } from '../utils/config'

const API_BASE = getApiBase()

interface JudgeStats {
  total_decisions: number
  verdict_distribution: Record<string, number>
  avg_latency_ms: number
  p95_latency_ms: number
  bypass_attempts_blocked: number
}

interface BypassPattern {
  id: string
  pattern_name: string
  canonical_name: string
  description: string
  severity: number
  is_active: boolean
}

interface BypassAttempt {
  id: string
  incident_id: string
  pattern_id: string
  detection_confidence: number
  blocked_at: string
}

const BYPASS_DESCRIPTIONS: Record<string, string> = {
  'Context Window Displacement': 'Inject 50,000+ benign tokens before a malicious payload, pushing it into the "lost in the middle" region. LLM judges fail; deterministic metadata catches it.',
  'Unicode Homoglyph Substitution': 'Replace ASCII characters with visually identical Unicode homoglyphs to evade string-based detection. NFKC normalization catches it.',
  'Indirect Tool Chaining': 'Split a malicious operation across multiple tool calls to evade per-call safety checks. Composite pattern detection catches it.',
  'Confidence Hijacking': 'Manipulate model confidence or claim authority to bypass safety checks. Binary enforcement ignores confidence.',
}

export default function JudgePage() {
  const [stats, setStats] = useState<JudgeStats | null>(null)
  const [patterns, setPatterns] = useState<BypassPattern[]>([])
  const [attempts, setAttempts] = useState<BypassAttempt[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [statsRes, patternsRes, attemptsRes] = await Promise.all([
        fetch(`${API_BASE}/judge/stats`),
        fetch(`${API_BASE}/judge/bypass-patterns`),
        fetch(`${API_BASE}/judge/bypass-attempts`),
      ])
      setStats(await statsRes.json())
      setPatterns(await patternsRes.json())
      setAttempts(await attemptsRes.json())
    } catch {
      // ignore
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  const verdictColor = (v: string) => {
    if (v === 'ALLOW') return 'text-green-600 bg-green-50'
    if (v === 'DENY') return 'text-red-600 bg-red-50'
    if (v === 'QUARANTINE') return 'text-orange-600 bg-orange-50'
    if (v === 'ESCALATE') return 'text-purple-600 bg-purple-50'
    return 'text-gray-600 bg-gray-50'
  }

  const verdictIcon = (v: string) => {
    if (v === 'ALLOW') return <CheckCircle className="w-4 h-4" />
    if (v === 'DENY') return <XCircle className="w-4 h-4" />
    if (v === 'QUARANTINE') return <Ban className="w-4 h-4" />
    return <UserCheck className="w-4 h-4" />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Judge Layer</h1>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 text-green-700 text-sm font-medium">
          <Lock className="w-4 h-4" />
          Deterministic Enforcement
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-5 h-5 text-blue-600" />}
          label="Total Decisions"
          value={String(stats?.total_decisions || 0)}
        />
        <StatCard
          icon={<Clock className="w-5 h-5 text-green-600" />}
          label="Avg Latency"
          value={`${stats?.avg_latency_ms?.toFixed(1) || 0}ms`}
        />
        <StatCard
          icon={<Clock className="w-5 h-5 text-orange-600" />}
          label="P95 Latency"
          value={`${stats?.p95_latency_ms?.toFixed(1) || 0}ms`}
        />
        <StatCard
          icon={<Shield className="w-5 h-5 text-red-600" />}
          label="Bypasses Blocked"
          value={String(stats?.bypass_attempts_blocked || 0)}
        />
      </div>

      {/* Verdict Distribution */}
      {stats && stats.verdict_distribution && Object.keys(stats.verdict_distribution).length > 0 && (
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Verdict Distribution</h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(stats.verdict_distribution).map(([verdict, count]) => (
              <div
                key={verdict}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg ${verdictColor(verdict)}`}
              >
                {verdictIcon(verdict)}
                <span className="text-sm font-medium">{verdict}</span>
                <span className="text-lg font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bypass Patterns */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-600" />
          Bypass Patterns — All Blocked
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patterns.map((pattern) => (
            <div
              key={pattern.id}
              className={`p-4 rounded-lg border ${
                pattern.is_active ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">{pattern.pattern_name}</h3>
                  <p className="text-xs text-gray-500 font-mono mt-0.5">{pattern.canonical_name}</p>
                </div>
                {pattern.is_active && (
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                    Active Threat
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {BYPASS_DESCRIPTIONS[pattern.canonical_name] || pattern.description}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <Shield className="w-4 h-4 text-green-600" />
                <span className="text-xs text-green-700 font-medium">Deterministic detection active</span>
              </div>
            </div>
          ))}
          {patterns.length === 0 && (
            <div className="col-span-2 text-center text-gray-500 py-8">
              No bypass patterns configured
            </div>
          )}
        </div>
      </div>

      {/* Recent Bypass Attempts */}
      {attempts.length > 0 && (
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Bypass Attempts</h2>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Incident</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Pattern</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Confidence</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Blocked At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {attempts.slice(0, 10).map((a) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-xs">{a.incident_id}</td>
                  <td className="px-3 py-2 text-gray-900">{a.pattern_id}</td>
                  <td className="px-3 py-2">{(a.detection_confidence * 100).toFixed(0)}%</td>
                  <td className="px-3 py-2 text-xs text-gray-500">
                    {new Date(a.blocked_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <p className="text-xl font-bold text-gray-900">{value}</p>
    </div>
  )
}
