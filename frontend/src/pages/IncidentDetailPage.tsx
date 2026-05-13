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
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface Incident {
  id: string
  incident_id: string
  incident_type: string
  severity: string
  status: string
  category: string
  event_id: string | null
  confidence: number
  judge_verdict: string | null
  bypass_detected: boolean
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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadIncident()
  }, [id])

  const loadIncident = async () => {
    setLoading(true)
    try {
      const [incRes, tlRes, forenRes] = await Promise.all([
        fetch(`${API_BASE}/incidents/${id}`),
        fetch(`${API_BASE}/incidents/${id}/timeline`),
        fetch(`${API_BASE}/incidents/${id}/forensics`),
      ])
      const incData = await incRes.json()
      const tlData = await tlRes.json()
      const forenData = await forenRes.json()
      setIncident(incData)
      setTimeline(tlData || [])
      setForensics(forenData.data || null)
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

  if (!incident) {
    return (
      <div className="space-y-6">
        <button onClick={() => navigate('/incidents')} className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
          <ArrowLeft className="w-4 h-4" /> Back to incidents
        </button>
        <div className="card p-8 text-center text-gray-500">Incident not found</div>
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

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Status" value={incident.status} />
        <StatCard label="Category" value={incident.category || '—'} />
        <StatCard label="Agent" value={incident.event_id || '—'} />
        <StatCard label="Confidence" value={`${(incident.confidence * 100).toFixed(0)}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline */}
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            Timeline
          </h2>
          {timeline.length === 0 ? (
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
              Forensics
            </h2>
            {forensics ? (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Package ID</span>
                  <span className="font-mono text-gray-900">{forensics.package_id}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Type</span>
                  <span className="text-gray-900">{forensics.package_type}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Integrity</span>
                  <span className="font-mono text-xs text-gray-900 truncate max-w-[200px]">
                    {forensics.integrity_hash}
                  </span>
                </div>
                {forensics.artifacts && forensics.artifacts.length > 0 && (
                  <div className="text-xs bg-gray-50 p-2 rounded">
                    <p className="font-medium text-gray-700 mb-1">Artifacts:</p>
                    <ul className="list-disc list-inside">
                      {forensics.artifacts.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No forensics data available</p>
            )}
          </div>

          <div className="card p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Metadata</h2>
            <p className="text-sm text-gray-500">Metadata available via forensics package</p>
          </div>
        </div>
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
