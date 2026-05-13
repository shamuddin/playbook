import { useEffect, useState } from 'react'
import {
  Shield,
  CheckCircle,
  AlertTriangle,
  FileText,
  ChevronDown,
  ChevronUp,
  GitCompare,
  Activity,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface Template {
  id: string
  template_id: string
  name: string
  description: string
  odp_set: Record<string, Record<string, string>>
}

interface Baseline {
  id: string
  incident_type: string
  severity: string
  severity_threshold: string
  auto_contain_enabled: boolean
  escalation_contacts: string[]
  response_time_sla_seconds: number
  forensic_level: string
  notify_targets: string[]
  compliance_report: boolean
  record_threshold: number
}

interface DryRunResult {
  incident_type: string
  odps_applied: number
  odps_skipped: number
  version: number
}

export default function PolicyBuilderPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [baselines, setBaselines] = useState<Baseline[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [expandedBaseline, setExpandedBaseline] = useState<string | null>(null)
  const [applying, setApplying] = useState(false)

  // Comparison state
  const [compareType, setCompareType] = useState<string>('AGT-DEL-001')
  const [compareResults, setCompareResults] = useState<Record<string, DryRunResult[]>>({})
  const [compareLoading, setCompareLoading] = useState(false)
  const [showComparison, setShowComparison] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/policy-builder/templates`).then((r) => r.json()),
      fetch(`${API_BASE}/policy-builder/nist-baseline`).then((r) => r.json()),
    ])
      .then(([tplRes, baseRes]) => {
        setTemplates(tplRes || [])
        setBaselines(baseRes.data?.items || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const applyTemplate = async (templateId: string) => {
    setApplying(true)
    try {
      const res = await fetch(
        `${API_BASE}/policy-builder/templates/${templateId}/apply`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ dry_run: false }),
        }
      )
      const data = await res.json()
      alert(data.message || 'Template applied')
    } catch {
      alert('Failed to apply template')
    }
    setApplying(false)
  }

  const runComparison = async () => {
    if (!compareType) return
    setCompareLoading(true)
    const results: Record<string, DryRunResult[]> = {}

    for (const tpl of templates) {
      try {
        const res = await fetch(
          `${API_BASE}/policy-builder/templates/${tpl.template_id}/apply`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              dry_run: true,
              incident_types: [compareType],
            }),
          }
        )
        const data = await res.json()
        results[tpl.template_id] = data.data?.results || []
      } catch {
        results[tpl.template_id] = []
      }
    }

    setCompareResults(results)
    setCompareLoading(false)
    setShowComparison(true)
  }

  // Get ODP values from a template for the selected incident type
  const getTemplateOdps = (template: Template, incidentType: string) => {
    return template.odp_set?.[incidentType] || {}
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  const selectedBaseline = baselines.find((b) => b.incident_type === compareType)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Policy Builder</h1>
      </div>

      {/* Template Comparison — Demo Hero */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-4">
          <GitCompare className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Template Comparison</h2>
          <span className="text-xs text-gray-500 ml-2">Same incident, different organizational responses</span>
        </div>

        <div className="flex flex-wrap gap-3 items-end mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Incident Type</label>
            <select
              value={compareType}
              onChange={(e) => setCompareType(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {baselines.map((b) => (
                <option key={b.incident_type} value={b.incident_type}>
                  {b.incident_type}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={runComparison}
            disabled={compareLoading}
            className="btn-primary py-2 px-4"
          >
            {compareLoading ? 'Comparing...' : 'Compare Templates'}
          </button>
        </div>

        {showComparison && selectedBaseline && (
          <div className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* NIST Baseline Column */}
              <div className="p-3 rounded-lg bg-gray-50 border border-gray-200">
                <h3 className="text-sm font-bold text-gray-900 mb-2 flex items-center gap-1">
                  <Shield className="w-4 h-4 text-blue-600" />
                  NIST Baseline
                </h3>
                <div className="space-y-2 text-xs">
                  <CompareRow label="Severity" value={selectedBaseline.severity} />
                  <CompareRow label="Auto Contain" value={selectedBaseline.auto_contain_enabled ? 'Yes' : 'No'} />
                  <CompareRow label="SLA" value={`${selectedBaseline.response_time_sla_seconds}s`} />
                  <CompareRow label="Forensics" value={selectedBaseline.forensic_level} />
                  <CompareRow label="Compliance" value={selectedBaseline.compliance_report ? 'Required' : 'Optional'} />
                  <CompareRow label="Record Threshold" value={String(selectedBaseline.record_threshold)} />
                </div>
              </div>

              {/* Template Columns */}
              {templates.map((tpl) => {
                const odps = getTemplateOdps(tpl, compareType)
                const result = compareResults[tpl.template_id]?.find((r) => r.incident_type === compareType)
                return (
                  <div
                    key={tpl.id}
                    className={`p-3 rounded-lg border ${
                      selectedTemplate === tpl.template_id
                        ? 'border-blue-300 bg-blue-50'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <h3 className="text-sm font-bold text-gray-900 mb-2">{tpl.name}</h3>
                    <div className="space-y-2 text-xs">
                      <CompareRow
                        label="Severity"
                        value={odps.severity_threshold || selectedBaseline.severity}
                        changed={!!odps.severity_threshold}
                      />
                      <CompareRow
                        label="Auto Contain"
                        value={odps.auto_contain_enabled === 'true' ? 'Yes' : odps.auto_contain_enabled === 'false' ? 'No' : selectedBaseline.auto_contain_enabled ? 'Yes' : 'No'}
                        changed={!!odps.auto_contain_enabled}
                      />
                      <CompareRow
                        label="SLA"
                        value={odps.response_time_sla ? `${odps.response_time_sla}s` : `${selectedBaseline.response_time_sla_seconds}s`}
                        changed={!!odps.response_time_sla}
                      />
                      <CompareRow
                        label="Forensics"
                        value={odps.forensic_level || selectedBaseline.forensic_level}
                        changed={!!odps.forensic_level}
                      />
                      <CompareRow
                        label="Compliance"
                        value={odps.compliance_report === 'true' ? 'Required' : odps.compliance_report === 'false' ? 'Optional' : selectedBaseline.compliance_report ? 'Required' : 'Optional'}
                        changed={!!odps.compliance_report}
                      />
                      <CompareRow
                        label="Record Threshold"
                        value={odps.record_threshold || String(selectedBaseline.record_threshold)}
                        changed={!!odps.record_threshold}
                      />
                    </div>
                    {result && (
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <span className="text-xs text-gray-500">
                          {result.odps_applied} changes, v{result.version}
                        </span>
                      </div>
                    )}
                    <button
                      onClick={() => {
                        setSelectedTemplate(tpl.template_id)
                        applyTemplate(tpl.template_id)
                      }}
                      disabled={applying}
                      className="mt-2 w-full text-xs py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      {applying && selectedTemplate === tpl.template_id ? 'Applying...' : 'Apply'}
                    </button>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Templates Section */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          Industry Templates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((tpl) => (
            <div
              key={tpl.id}
              className={`card p-4 cursor-pointer transition-all ${
                selectedTemplate === tpl.template_id
                  ? 'ring-2 ring-blue-500'
                  : 'hover:shadow-md'
              }`}
              onClick={() => setSelectedTemplate(tpl.template_id)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">{tpl.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">{tpl.template_id}</p>
                </div>
                <Shield className="w-5 h-5 text-gray-400" />
              </div>
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">{tpl.description}</p>
              <div className="mt-3 flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  {Object.keys(tpl.odp_set || {}).length} incident types
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* NIST Baselines Section */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          NIST Baselines
        </h2>
        <div className="space-y-2">
          {baselines.map((base) => (
            <div key={base.id} className="card overflow-hidden">
              <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                onClick={() =>
                  setExpandedBaseline(
                    expandedBaseline === base.incident_type ? null : base.incident_type
                  )
                }
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      base.severity === 'critical'
                        ? 'bg-red-100 text-red-700'
                        : base.severity === 'high'
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {base.severity.toUpperCase()}
                  </span>
                  <span className="font-medium text-gray-900">{base.incident_type}</span>
                </div>
                <div className="flex items-center gap-2">
                  {base.auto_contain_enabled && (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  )}
                  {base.compliance_report && (
                    <FileText className="w-4 h-4 text-blue-500" />
                  )}
                  {expandedBaseline === base.incident_type ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </div>
              </div>

              {expandedBaseline === base.incident_type && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <BaselineField
                      label="Severity Threshold"
                      value={base.severity_threshold}
                    />
                    <BaselineField
                      label="Auto Contain"
                      value={base.auto_contain_enabled ? 'Enabled' : 'Disabled'}
                      warning={!base.auto_contain_enabled}
                    />
                    <BaselineField
                      label="Response SLA"
                      value={`${base.response_time_sla_seconds}s`}
                    />
                    <BaselineField
                      label="Forensic Level"
                      value={base.forensic_level}
                    />
                    <BaselineField
                      label="Record Threshold"
                      value={base.record_threshold.toString()}
                    />
                    <BaselineField
                      label="Compliance Report"
                      value={base.compliance_report ? 'Required' : 'Optional'}
                    />
                    <BaselineField
                      label="Escalation"
                      value={`${base.escalation_contacts.length} contacts`}
                    />
                    <BaselineField
                      label="Notify"
                      value={`${base.notify_targets.length} targets`}
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function BaselineField({
  label,
  value,
  warning,
}: {
  label: string
  value: string
  warning?: boolean
}) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p
        className={`text-sm font-medium ${
          warning ? 'text-orange-600 flex items-center gap-1' : 'text-gray-900'
        }`}
      >
        {warning && <AlertTriangle className="w-3 h-3" />}
        {value}
      </p>
    </div>
  )
}

function CompareRow({
  label,
  value,
  changed,
}: {
  label: string
  value: string
  changed?: boolean
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={`font-medium ${changed ? 'text-blue-700' : 'text-gray-900'}`}>
        {changed && <Activity className="w-3 h-3 inline mr-1" />}
        {value}
      </span>
    </div>
  )
}
