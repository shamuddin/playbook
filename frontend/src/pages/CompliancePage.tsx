import { useEffect, useState } from 'react'
import { FileText, Shield, AlertTriangle, CheckCircle, BookOpen, Sparkles, Info, ChevronDown, ChevronUp } from 'lucide-react'

import { getApiBase } from '../utils/config'
import { apiFetch } from '../utils/api'

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
  const [aiReport, setAiReport] = useState<any>(null)
  const [aiReportLoading, setAiReportLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showHelp, setShowHelp] = useState(false)

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
      const res = await apiFetch(`${API_BASE}/compliance/frameworks`)
      if (!res.ok) throw new Error('Unauthorized')
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
        apiFetch(`${API_BASE}/compliance/mapping?framework=${framework}`),
        apiFetch(`${API_BASE}/compliance/gap-analysis?framework=${framework}`),
      ])
      if (mapRes.ok) {
        const mapData = await mapRes.json()
        setMappings(Array.isArray(mapData) ? mapData : (mapData.data || []))
      }
      if (gapRes.ok) setGapAnalysis((await gapRes.json()).data || null)
    } catch {
      setMappings([])
      setGapAnalysis(null)
    }
    setAiReport(null)
  }

  const generateAiReport = async () => {
    if (!selectedFramework) return
    setAiReportLoading(true)
    try {
      const res = await apiFetch(
        `${API_BASE}/compliance/gemini-report?framework=${selectedFramework}`,
        { method: 'POST' }
      )
      if (res.ok) {
        const data = await res.json()
        setAiReport(data.data?.report || null)
      }
    } catch {
      // silent fail
    }
    setAiReportLoading(false)
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
          <p className="text-sm text-gray-500 mt-1">
            Map incidents to regulatory frameworks and identify gaps.
          </p>
        </div>
        <button
          onClick={generateAiReport}
          disabled={aiReportLoading || !selectedFramework}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white text-sm font-semibold rounded-lg shadow transition-colors"
        >
          <Sparkles className="w-4 h-4" />
          {aiReportLoading ? 'Generating...' : 'AI Report'}
        </button>
      </div>

      {/* Help / Guide Panel */}
      <div className="card p-4 bg-blue-50 border-l-4 border-blue-500">
        <button
          onClick={() => setShowHelp((s) => !s)}
          className="flex items-center gap-2 text-sm font-semibold text-blue-800 w-full"
        >
          <Info className="w-4 h-4" />
          What am I looking at?
          {showHelp ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
        </button>
        {showHelp && (
          <div className="mt-3 space-y-3 text-sm text-blue-900">
            <p>
              <strong>Compliance Mapping</strong> shows how your PLAYBOOK incident types map to specific controls in regulatory frameworks like the <strong>EU AI Act</strong> and <strong>NIST AI RMF</strong>.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2">
              <div className="bg-white p-3 rounded-lg border border-blue-200">
                <p className="font-semibold text-gray-900 mb-1">Coverage Analysis</p>
                <p className="text-xs text-gray-600">Shows what percentage of incident types are covered by the selected framework. Red gaps mean you have no controls for those incidents.</p>
              </div>
              <div className="bg-white p-3 rounded-lg border border-blue-200">
                <p className="font-semibold text-gray-900 mb-1">Control Mapping</p>
                <p className="text-xs text-gray-600">Each card links an incident type (e.g., Data Exfiltration) to a specific regulatory control (e.g., Article 15). The confidence score shows how well PLAYBOOK enforces it.</p>
              </div>
              <div className="bg-white p-3 rounded-lg border border-blue-200">
                <p className="font-semibold text-gray-900 mb-1">AI Report</p>
                <p className="text-xs text-gray-600">One click generates a board-ready narrative: your current posture, critical gaps, and prioritized next steps using Gemini.</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Framework Selector */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <BookOpen className="w-5 h-5 text-blue-600" />
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-500 mb-1">Framework</label>
            <select
              value={selectedFramework}
              onChange={(e) => setSelectedFramework(e.target.value)}
              className="w-full min-w-[240px] px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {frameworks.map((fw) => (
                <option key={fw.name} value={fw.name}>
                  {fw.display_name} ({fw.version})
                </option>
              ))}
            </select>
          </div>
          {selectedFramework && (
            <div className="hidden md:block text-xs text-gray-500 max-w-md">
              {selectedFramework === 'eu_ai_act' && 'European Union regulation on artificial intelligence. Covers risk management, accuracy, and incident reporting obligations for AI systems.'}
              {selectedFramework === 'nist_ai_rmf' && 'NIST AI Risk Management Framework. Provides guidance on governing, mapping, measuring, and managing AI risks across the organization.'}
              {selectedFramework === 'hipaa' && 'Health Insurance Portability and Accountability Act. Protects patient health information and requires breach notification.'}
              {selectedFramework === 'soc2' && 'Service Organization Control 2. Audits security, availability, processing integrity, confidentiality, and privacy.'}
              {selectedFramework === 'gdpr' && 'General Data Protection Regulation. EU law on data protection and privacy for individuals.'}
            </div>
          )}
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

      {/* AI Compliance Report */}
      {aiReport && (
        <div className="card p-5 border-l-4 border-purple-500 bg-purple-50">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <h2 className="text-lg font-semibold text-purple-900">Gemini Compliance Report</h2>
          </div>
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="text-xs font-bold text-purple-700 uppercase tracking-wide mb-2">Overview</h3>
              <p className="text-sm text-gray-700">{aiReport.overview}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="text-xs font-bold text-purple-700 uppercase tracking-wide mb-2">Critical Gaps</h3>
              <p className="text-sm text-gray-700">{aiReport.critical_gaps}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="text-xs font-bold text-purple-700 uppercase tracking-wide mb-2">Recommendations</h3>
              <p className="text-sm text-gray-700">{aiReport.recommendations}</p>
            </div>
          </div>
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
