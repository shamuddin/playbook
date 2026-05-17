import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserCheck, Clock, AlertTriangle, CheckCircle, ThumbsUp, ThumbsDown, ShieldAlert, RotateCcw } from 'lucide-react'

import { getApiBase } from '../utils/config'
import { apiFetch } from '../utils/api'

const API_BASE = getApiBase()

interface Incident {
  id: string
  incident_id: string
  incident_type: string
  severity: string
  status: string
  agent_id: string
  confidence: number
  judge_verdict: string | null
  bypass_detected: boolean
  created_at: string
  description: string
}

export default function ReviewQueuePage() {
  const navigate = useNavigate()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadQueue()
  }, [])

  const loadQueue = async () => {
    setLoading(true)
    try {
      // Fetch escalated incidents and those with ESCALATE verdict
      const params = new URLSearchParams()
      params.set('page_size', '100')
      params.set('status', 'escalated')
      const res = await apiFetch(`${API_BASE}/incidents?${params.toString()}`)
      if (!res.ok) throw new Error('Unauthorized')
      const data = await res.json()
      let items = data.data || []

      // Also fetch all incidents and filter for ESCALATE verdict or pending human review
      const allRes = await apiFetch(`${API_BASE}/incidents?page_size=100`)
      if (!allRes.ok) throw new Error('Unauthorized')
      const allData = await allRes.json()
      const escalateItems = (allData.data || []).filter(
        (i: Incident) =>
          (i.judge_verdict === 'ESCALATE' || i.status === 'detected' || i.status === 'classified') &&
          !items.find((x: Incident) => x.id === i.id)
      )
      items = [...items, ...escalateItems]
      setIncidents(items)
    } catch {
      setIncidents([])
    }
    setLoading(false)
  }

  const handleAction = async (incidentId: string, action: string) => {
    setActionLoading(`${incidentId}-${action}`)
    try {
      let status = incidentId
      if (action === 'acknowledge') status = 'investigating'
      else if (action === 'approve') status = 'resolved'
      else if (action === 'deny') status = 'false_positive'
      else if (action === 'escalate') status = 'escalated'

      const res = await apiFetch(`${API_BASE}/incidents/${incidentId}/status?status=${status}`, {
        method: 'PUT',
      })
      if (res.ok) {
        setIncidents((prev) => prev.filter((i) => i.incident_id !== incidentId))
      } else {
        const err = await res.json().catch(() => ({}))
        alert(err.detail || `Failed to ${action} incident`)
      }
    } catch (err: any) {
      alert(`Failed to ${action}: ` + (err.message || 'Network error'))
    }
    setActionLoading(null)
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Review Queue</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={loadQueue}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
            title="Refresh queue"
          >
            <RotateCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-50 text-amber-700 text-sm font-medium">
            <UserCheck className="w-4 h-4" />
            {incidents.length} pending
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : incidents.length === 0 ? (
        <div className="card p-8 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h2 className="text-lg font-medium text-gray-900">Queue Clear</h2>
          <p className="text-sm text-gray-500 mt-1">No incidents require human review</p>
        </div>
      ) : (
        <div className="space-y-3">
          {incidents.map((inc) => (
            <div
              key={inc.id}
              onClick={() => navigate(`/incidents/${inc.incident_id}`)}
              className="card p-4 cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityBadge(inc.severity)}`}>
                      {inc.severity}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">{inc.incident_id}</span>
                    {inc.bypass_detected && (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs font-medium">
                        <AlertTriangle className="w-3 h-3" /> Bypass
                      </span>
                    )}
                  </div>
                  <h3 className="font-medium text-gray-900">{inc.incident_type}</h3>
                  <p className="text-sm text-gray-600 mt-0.5">{inc.description || 'No description'}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>Agent: {inc.agent_id}</span>
                    <span>Confidence: {(inc.confidence * 100).toFixed(0)}%</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(inc.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
                    {inc.judge_verdict || 'ESCALATED'}
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleAction(inc.incident_id, 'acknowledge')
                      }}
                      disabled={!!actionLoading}
                      title="Acknowledge — start investigation"
                      className="p-1.5 rounded hover:bg-blue-100 text-blue-600 disabled:opacity-50"
                    >
                      <CheckCircle className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleAction(inc.incident_id, 'approve')
                      }}
                      disabled={!!actionLoading}
                      title="Approve — mark as resolved"
                      className="p-1.5 rounded hover:bg-green-100 text-green-600 disabled:opacity-50"
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleAction(inc.incident_id, 'deny')
                      }}
                      disabled={!!actionLoading}
                      title="Deny — mark as false positive"
                      className="p-1.5 rounded hover:bg-red-100 text-red-600 disabled:opacity-50"
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleAction(inc.incident_id, 'escalate')
                      }}
                      disabled={!!actionLoading}
                      title="Escalate — send to senior analyst"
                      className="p-1.5 rounded hover:bg-orange-100 text-orange-600 disabled:opacity-50"
                    >
                      <ShieldAlert className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
