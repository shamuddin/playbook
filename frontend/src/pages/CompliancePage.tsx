import { useEffect, useState } from 'react'
import { FileText, Shield, AlertTriangle, CheckCircle, BookOpen } from 'lucide-react'

import { getApiBase } from '../utils/config'

const API_BASE = getApiBase()

interface Framework {
  name: string
  display_name: string
  version: string
}

interface Mapping {
  incident_type: string
  framework: string
  control_id: string
  control_name: string
  risk_level: string
  confidence: number
}

interface GapAnalysis {
  framework: string
  total_incident_types: number
  covered_types: number
  coverage_percentage: number
  critical_gaps: Array<{
    incident_type: string
    name: string
    missing_controls: number
  }>
  uncovered: Array<{
    incident_type: string
    name: string
  }>
}

export default function CompliancePage() {
  const [frameworks, setFrameworks] = useState<Framework[]>([])
  const [mappings, setMappings] = useState<Mapping[]>([])
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null)
  const [selectedFramework, setSelectedFramework] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFrameworks()
  }, [])

  useEffect(() => {
    if (selectedFramework) {
      loadMappings(selectedFramework)
    }
  }, [selectedFramework])

  const loadFrameworks = async () => {
    try {
      const res = await fetch(`${API_BASE}/compliance/frameworks`)
      const data = await res.json()
      const fw = data.data?.frameworks || []
      setFrameworks(fw)
      if (fw.length > 0) {
        setSelectedFramework(fw[0].name)
      }
    } catch {
      // ignore
    }
    setLoading(false)
  }

  const loadMappings = async (framework: string) => {
    try {
      const [mapRes, gapRes] = await Promise.all([
        fetch(`${API_BASE}/compliance/mapping?framework=${framework}`),
        fetch(`${API_BASE}/compliance/gap-analysis?framework=${framework}`),
      ])
      setMappings(await mapRes.json())
      const gapData = await gapRes.json()
      setGapAnalysis(gapData.data || null)
    } catch {
      setMappings([])
      setGapAnalysis(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  const riskColor = (risk: string) => {
    if (risk === 'high') return 'text-red-600 bg-red-50'
    if (risk === 'medium') return 'text-orange-600 bg-orange-50'
    if (risk === 'low') return 'text-green-600 bg-green-50'
    return 'text-gray-600 bg-gray-50'
  }

  const uniqueIncidentTypes = Array.from(new Set(mappings.map((m) => m.incident_type)))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
      </div>

      {/* Framework Selector */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <BookOpen className="w-5 h-5 text-blue-600" />
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Framework</label>
            <select
              value={selectedFramework}
              onChange={(e) => setSelectedFramework(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {frameworks.map((fw) => (
                <option key={fw.name} value={fw.name}>
                  {fw.display_name} ({fw.version})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Gap Analysis */}
      {gapAnalysis && (
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-600" />
            Coverage Analysis
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500">Total Incident Types</p>
              <p className="text-xl font-bold text-gray-900">{gapAnalysis.total_incident_types}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-xs text-gray-500">Covered Types</p>
              <p className="text-xl font-bold text-green-700">{gapAnalysis.covered_types}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-gray-500">Coverage</p>
              <p className="text-xl font-bold text-blue-700">{gapAnalysis.coverage_percentage?.toFixed(1) || 0}%</p>
            </div>
          </div>
          {gapAnalysis.critical_gaps && gapAnalysis.critical_gaps.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                Critical Gaps ({gapAnalysis.critical_gaps.length})
              </h3>
              <div className="space-y-2">
                {gapAnalysis.critical_gaps.map((gap, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-orange-50 rounded text-sm">
                    <span className="font-mono text-xs text-orange-700">{gap.incident_type}</span>
                    <span className="text-gray-700">{gap.name}</span>
                    <span className="text-xs text-gray-500 ml-auto">{gap.missing_controls} missing</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Mapping Matrix */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          Control Mapping
        </h2>
        {mappings.length === 0 ? (
          <p className="text-sm text-gray-500">No mappings found for this framework</p>
        ) : (
          <div className="space-y-6">
            {uniqueIncidentTypes.map((incidentType) => (
              <div key={incidentType}>
                <h3 className="text-sm font-medium text-gray-700 mb-2">{incidentType}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {mappings
                    .filter((m) => m.incident_type === incidentType)
                    .map((m, i) => (
                      <div
                        key={i}
                        className={`p-3 rounded-lg border ${riskColor(m.risk_level).replace('text-', 'border-').replace('50', '200')}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs text-gray-500">{m.control_id}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${riskColor(m.risk_level)}`}>
                            {m.risk_level}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-gray-900 mt-1">{m.control_name}</p>
                        <div className="flex items-center gap-1 mt-2">
                          <CheckCircle className="w-3 h-3 text-green-500" />
                          <span className="text-xs text-gray-500">
                            {(m.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
