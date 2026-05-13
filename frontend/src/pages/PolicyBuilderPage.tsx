import { useEffect, useState } from 'react'
import {
  Shield,
  CheckCircle,
  AlertTriangle,
  FileText,
  ChevronDown,
  ChevronUp,
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

export default function PolicyBuilderPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [baselines, setBaselines] = useState<Baseline[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [expandedBaseline, setExpandedBaseline] = useState<string | null>(null)
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/policy-builder/templates`).then((r) => r.json()),
      fetch(`${API_BASE}/policy-builder/nist-baseline`).then((r) => r.json()),
    ])
      .then(([tplRes, baseRes]) => {
        setTemplates(tplRes || [])
        setBaselines(baseRes.data || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const applyTemplate = async (templateId: string) => {
    setApplying(true)
    try {
      const res = await fetch(
        `${API_BASE}/policy-builder/templates/${templateId}/apply`,
        { method: 'POST' }
      )
      const data = await res.json()
      alert(data.message || 'Template applied')
    } catch {
      alert('Failed to apply template')
    }
    setApplying(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Policy Builder</h1>
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
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                {tpl.description}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  {Object.keys(tpl.odp_set || {}).length} incident types
                </span>
              </div>
              {selectedTemplate === tpl.template_id && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    applyTemplate(tpl.template_id)
                  }}
                  disabled={applying}
                  className="mt-3 w-full btn-primary text-sm py-1.5"
                >
                  {applying ? 'Applying...' : 'Apply Template'}
                </button>
              )}
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
                  <span className="font-medium text-gray-900">
                    {base.incident_type}
                  </span>
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
