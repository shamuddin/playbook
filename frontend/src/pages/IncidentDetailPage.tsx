import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  AlertTriangle,
  Shield,
  Clock,
  Activity,
  FileText,
  CheckCircle,
  XCircle,
  Ban,
  UserCheck,
  Sparkles,
  Loader2,
} from 'lucide-react'

import { getApiBase } from '../utils/config'
import { apiFetch } from '../utils/api'

const API_BASE = getApiBase()

interface Incident {
  id: string
  incident_id: string
  incident_type: string
  severity: string
  status: string
  category: string
  event_id: string | null
  agent_id: string | null
  swarm_id: string | null
  confidence: number
  judge_verdict: string | null
  bypass_detected: boolean
  response_status: string
  created_at: string
  updated_at: string
}

interface TimelineEvent {
  id: string
  timestamp: string
  stage: string
  event_type: string
  event_description: string
  source_component: string
  details_json: Record<string, any>
}

interface ForensicsData {
  package_id: string
  incident_id: string
  package_type: string
  is_verified: boolean
  integrity_hash: string
  artifacts: string[]
  manifest: Record<string, any>
  signature: Record<string, any>
  generated_at: string | null
}

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [forensics, setForensics] = useState<ForensicsData | null>(null)
  const [timelineError, setTimelineError] = useState(false)
  const [forensicsError, setForensicsError] = useState(false)
  const [loadError, setLoadError] = useState(false)
  const [geminiAnalysis, setGeminiAnalysis] = useState<any>(null)
  const [geminiLoading, setGeminiLoading] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadIncident()
    loadGeminiAnalysis()
  }, [id])

  const loadIncident = async () => {
    setLoading(true)
    setLoadError(false)
    setTimelineError(false)
    setForensicsError(false)
    try {
      const [incRes, tlRes, forenRes] = await Promise.all([
        apiFetch(`${API_BASE}/incidents/${id}`),
        apiFetch(`${API_BASE}/incidents/${id}/timeline`),
        apiFetch(`${API_BASE}/incidents/${id}/forensics`),
      ])
      if (incRes.ok) {
        setIncident(await incRes.json())
      } else {
        setLoadError(true)
      }
      if (tlRes.ok) {
        setTimeline((await tlRes.json()) || [])
      } else {
        setTimelineError(true)
      }
      if (forenRes.ok) {
        setForensics((await forenRes.json()).data || null)
      } else {
        setForensicsError(true)
      }
    } catch {
      setLoadError(true)
    }
    setLoading(false)
  }

  const loadGeminiAnalysis = async () => {
    if (!id) return
    setGeminiLoading(true)
    try {
      const res = await apiFetch(`${API_BASE}/incidents/${id}/gemini-analysis`)
      if (res.ok) {
        const data = await res.json()
        setGeminiAnalysis(data.data?.analysis || null)
      }
    } catch {
      // silent fail — analysis is optional
    }
    setGeminiLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="space-y-6">
        <button onClick={() => navigate('/incidents')} className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
          <ArrowLeft className="w-4 h-4" /> Back to incidents
        </button>
        <div className="card p-8 text-center">
          <p className="text-gray-500 mb-4">
            {loadError ? 'Failed to load incident data. The server may be unavailable.' : 'Incident not found'}
          </p>
          {loadError && (
            <button
              onClick={loadIncident}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  const severityColor = (s: string) => {
    if (s === 'critical') return 'text-red-600 bg-red-50 border-red-200'
    if (s === 'high') return 'text-orange-600 bg-orange-50 border-orange-200'
    if (s === 'medium') return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-green-600 bg-green-50 border-green-200'
  }

  const verdictIcon = (v: string | null) => {
    if (!v) return <span className="text-gray-400">—</span>
    if (v === 'ALLOW') return <CheckCircle className="w-5 h-5 text-green-500" />
    if (v === 'DENY') return <XCircle className="w-5 h-5 text-red-500" />
    if (v === 'QUARANTINE') return <Ban className="w-5 h-5 text-orange-500" />
    return <UserCheck className="w-5 h-5 text-purple-500" />
  }

  const stageIcon = (stage: string) => {
    if (stage === 'DETECT') return <Activity className="w-4 h-4 text-blue-500" />
    if (stage === 'CLASSIFY') return <Shield className="w-4 h-4 text-purple-500" />
    if (stage === 'JUDGE') return <UserCheck className="w-4 h-4 text-orange-500" />
    if (stage === 'RESPOND') return <AlertTriangle className="w-4 h-4 text-red-500" />
    if (stage === 'FORENSICS') return <FileText className="w-4 h-4 text-green-500" />
    return <Clock className="w-4 h-4 text-gray-400" />
  }

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/incidents')} className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
        <ArrowLeft className="w-4 h-4" /> Back to incidents
      </button>

      {/* Judge Denied Banner */}
      {incident.judge_verdict === 'DENY' && (
        <div className="bg-red-600 text-white px-6 py-3 rounded-lg flex items-center gap-3 shadow-lg">
          <AlertTriangle className="w-5 h-5" />
          <span className="font-bold uppercase tracking-wide">JUDGE DENIED — AUTO-CONTAINMENT INITIATED</span>
        </div>
      )}

      {/* Quarantine Visualization */}
      {(incident.judge_verdict === 'DENY' || incident.judge_verdict === 'QUARANTINE') && (
        <div className="card p-5 border-2 border-orange-400 bg-orange-50">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
              <Ban className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-orange-800 uppercase tracking-wide">Lobster Trap Quarantine</h3>
              <p className="text-xs text-orange-600">Deep Packet Inspection for AI — Agent output isolated</p>
            </div>
            <span className="ml-auto px-3 py-1 bg-orange-200 text-orange-800 text-xs font-bold rounded-full animate-pulse">
              ACTIVE
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white p-3 rounded-lg border border-orange-200 text-center">
              <p className="text-xs text-gray-500">Agent</p>
              <p className="text-sm font-mono font-medium text-gray-900 truncate">{incident.agent_id || 'N/A'}</p>
            </div>
            <div className="bg-white p-3 rounded-lg border border-orange-200 text-center">
              <p className="text-xs text-gray-500">Status</p>
              <p className="text-sm font-medium text-orange-700">ISOLATED</p>
            </div>
            <div className="bg-white p-3 rounded-lg border border-orange-200 text-center">
              <p className="text-xs text-gray-500">Action Blocked</p>
              <p className="text-sm font-medium text-red-700">{incident.incident_type}</p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className={`card p-6 border-l-4 ${severityColor(incident.severity).split(' ').pop()}`}>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className={`px-2.5 py-1 rounded text-xs font-bold uppercase ${severityColor(incident.severity)}`}>
                {incident.severity}
              </span>
              <span className="text-xs text-gray-500 font-mono">{incident.incident_id}</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">
              {incident.incident_type}
            </h1>
            <p className="text-sm text-gray-600 mt-1">Event: {incident.event_id || 'Unknown'}</p>
            {incident.agent_id && (
              <p className="text-sm text-gray-600 mt-0.5">Agent: {incident.agent_id}</p>
            )}
            {incident.swarm_id && (
              <p className="text-sm text-gray-600 mt-0.5">Swarm: {incident.swarm_id}</p>
            )}
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end">
              {incident.bypass_detected && (
                <span className="flex items-center gap-1 px-2 py-1 rounded bg-red-100 text-red-700 text-xs font-medium">
                  <AlertTriangle className="w-3 h-3" /> Bypass Detected
                </span>
              )}
              {verdictIcon(incident.judge_verdict)}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {new Date(incident.created_at).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Pipeline Visualization */}
      <PipelineVisualization
        stages={[
          { id: 'DETECT', label: 'Detect', icon: <Activity className="w-4 h-4" />, status: 'completed', latency: '12ms' },
          { id: 'CLASSIFY', label: 'Classify', icon: <Shield className="w-4 h-4" />, status: 'completed', latency: '8ms' },
          { id: 'JUDGE', label: 'Judge', icon: <UserCheck className="w-4 h-4" />, status: incident.judge_verdict ? 'completed' : 'active', latency: '15ms' },
          { id: 'RESPOND', label: 'Enforce', icon: <AlertTriangle className="w-4 h-4" />, status: incident.response_status === 'completed' ? 'completed' : incident.response_status === 'pending' ? 'pending' : 'active' },
        ]}
      />

      {/* Gemini AI Security Analysis */}
      <div className="card p-5 border-l-4 border-purple-500 bg-purple-50">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-purple-600" />
          <h2 className="text-lg font-semibold text-purple-900">Gemini Security Analysis</h2>
          {geminiLoading && <Loader2 className="w-4 h-4 text-purple-500 animate-spin" />}
        </div>
        {geminiAnalysis ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="text-xs font-bold text-purple-700 uppercase tracking-wide mb-2">Threat Analysis</h3>
              <p className="text-sm text-gray-700">{geminiAnalysis.threat_analysis}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="text-xs font-bold text-purple-700 uppercase tracking-wide mb-2">Impact Assessment</h3>
              <p className="text-sm text-gray-700">{geminiAnalysis.impact_assessment}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="text-xs font-bold text-purple-700 uppercase tracking-wide mb-2">Remediation</h3>
              <p className="text-sm text-gray-700">{geminiAnalysis.remediation}</p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">{geminiLoading ? 'Generating AI analysis...' : 'AI analysis unavailable'}</p>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Status" value={incident.status} />
        <StatCard label="Category" value={incident.category || '—'} />
        <StatCard label="Agent" value={incident.agent_id || '—'} />
        <StatCard label="Confidence" value={`${(incident.confidence * 100).toFixed(0)}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline */}
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            Timeline
          </h2>
          {timelineError ? (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">Failed to load timeline events</p>
            </div>
          ) : timeline.length === 0 ? (
            <p className="text-sm text-gray-500">No timeline events</p>
          ) : (
            <div className="space-y-4">
              {timeline.map((event, i) => (
                <div key={event.id} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                      {stageIcon(event.stage)}
                    </div>
                    {i < timeline.length - 1 && (
                      <div className="w-0.5 flex-1 bg-gray-200 my-1" />
                    )}
                  </div>
                  <div className="pb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-gray-500">{event.stage}</span>
                      <span className="text-xs text-gray-400">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-900 mt-0.5">{event.event_description}</p>
                    <p className="text-xs text-gray-500">{event.source_component}</p>
                    {Object.keys(event.details_json).length > 0 && (
                      <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                        {JSON.stringify(event.details_json, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Forensics & Metadata */}
        <div className="space-y-6">
          <div className="card p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              Forensics Evidence Package
            </h2>
            {forensicsError ? (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">Failed to load forensics data</p>
              </div>
            ) : forensics ? (
              <div className="space-y-4">
                {/* Detection Summary */}
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Detection Summary</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="text-gray-500">Type:</span> <span className="font-medium text-gray-900">{incident?.incident_type}</span></div>
                    <div><span className="text-gray-500">Severity:</span> <span className={`font-medium ${incident?.severity === 'critical' ? 'text-red-600' : incident?.severity === 'high' ? 'text-orange-600' : 'text-gray-900'}`}>{incident?.severity}</span></div>
                    <div><span className="text-gray-500">Confidence:</span> <span className="font-medium text-gray-900">{(incident?.confidence || 0) * 100}%</span></div>
                    <div><span className="text-gray-500">Category:</span> <span className="font-medium text-gray-900">{incident?.category || '—'}</span></div>
                  </div>
                </div>

                {/* Judge Decision */}
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Judge Decision</p>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                      incident?.judge_verdict === 'DENY' ? 'bg-red-100 text-red-700' :
                      incident?.judge_verdict === 'ALLOW' ? 'bg-green-100 text-green-700' :
                      incident?.judge_verdict === 'QUARANTINE' ? 'bg-orange-100 text-orange-700' :
                      'bg-purple-100 text-purple-700'
                    }`}>
                      {incident?.judge_verdict || 'PENDING'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    {incident?.judge_verdict === 'DENY' ? 'Action blocked. Agent output isolated before reaching downstream systems.' :
                     incident?.judge_verdict === 'ALLOW' ? 'Action permitted. No risk indicators triggered.' :
                     incident?.judge_verdict === 'QUARANTINE' ? 'Agent isolated pending human review.' :
                     incident?.judge_verdict === 'ESCALATE' ? 'Forwarded to human analyst queue.' :
                     'Awaiting judge evaluation...'}
                  </p>
                </div>

                {/* Evidence Package */}
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Evidence Package</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Package ID</span>
                      <span className="font-mono text-gray-900">{forensics.package_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Type</span>
                      <span className="text-gray-900">{forensics.package_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Integrity (SHA-256)</span>
                      <span className="font-mono text-xs text-gray-900 truncate max-w-[180px]">
                        {forensics.integrity_hash}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Verified</span>
                      <span className={forensics.is_verified ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                        {forensics.is_verified ? 'Yes — tamper-evident' : 'Pending verification'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Artifacts */}
                {forensics.artifacts && forensics.artifacts.length > 0 && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Artifacts</p>
                    <div className="grid grid-cols-2 gap-2">
                      {forensics.artifacts.map((a, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm bg-white p-2 rounded border border-gray-200">
                          <FileText className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-700">{a}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Manifest */}
                {forensics.manifest && Object.keys(forensics.manifest).length > 0 && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Manifest</p>
                    <pre className="text-xs text-gray-700 overflow-x-auto">
                      {JSON.stringify(forensics.manifest, null, 2)}
                    </pre>
                  </div>
                )}

                <button
                  onClick={() => navigate(`/forensics/${incident?.incident_id}`)}
                  className="w-full text-center text-sm text-blue-600 hover:text-blue-700 py-2 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  View Full Forensics Report →
                </button>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No forensics data available</p>
            )}
          </div>

          <div className="card p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Metadata</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Agent ID</span> <span className="font-mono text-gray-900">{incident?.agent_id || '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Swarm ID</span> <span className="font-mono text-gray-900">{incident?.swarm_id || '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Event ID</span> <span className="font-mono text-gray-900">{incident?.event_id || '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Created</span> <span className="text-gray-900">{incident?.created_at ? new Date(incident.created_at).toLocaleString() : '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Updated</span> <span className="text-gray-900">{incident?.updated_at ? new Date(incident.updated_at).toLocaleString() : '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Response Status</span> <span className="text-gray-900">{incident?.response_status || '—'}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PipelineVisualization({
  stages,
}: {
  stages: Array<{
    id: string
    label: string
    icon: React.ReactNode
    status: 'completed' | 'active' | 'pending'
    latency?: string
  }>
}) {
  return (
    <div className="card p-5">
      <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Activity className="w-4 h-4 text-blue-600" />
        Incident Response Pipeline
      </h2>
      <div className="flex items-center gap-2">
        {stages.map((stage, i) => (
          <div key={stage.id} className="contents">
            <div
              className={`flex-1 flex flex-col items-center gap-2 p-3 rounded-lg border transition-all ${
                stage.status === 'completed'
                  ? 'bg-green-50 border-green-200'
                  : stage.status === 'active'
                  ? 'bg-blue-50 border-blue-200 ring-2 ring-blue-300'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  stage.status === 'completed'
                    ? 'bg-green-500 text-white'
                    : stage.status === 'active'
                    ? 'bg-blue-600 text-white animate-pulse'
                    : 'bg-gray-300 text-white'
                }`}
              >
                {stage.status === 'completed' ? <CheckCircle className="w-4 h-4" /> : stage.icon}
              </div>
              <div className="text-center">
                <p className="text-xs font-semibold text-gray-700">{stage.label}</p>
                {stage.latency && (
                  <p className="text-[10px] text-gray-500">{stage.latency}</p>
                )}
              </div>
            </div>
            {i < stages.length - 1 && (
              <div className="w-6 h-0.5 bg-gray-300" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-semibold text-gray-900 mt-0.5">{value}</p>
    </div>
  )
}
