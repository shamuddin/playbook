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
  Save,
  RotateCcw,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1'

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

interface ConflictItem {
  conflict_type: string
  severity: string
  message: string
  expected_value?: string
  actual_value?: string
}

interface ODPFormState {
  severity_threshold: string
  auto_contain_enabled: string
  escalation_contacts: string
  response_time_sla: string
  forensic_level: string
  notify_targets: string
  compliance_report: string
  record_threshold: string
}

function baselineToForm(base: Baseline): ODPFormState {
  return {
    severity_threshold: base.severity,
    auto_contain_enabled: String(base.auto_contain_enabled),
    escalation_contacts: JSON.stringify(base.escalation_contacts || []),
    response_time_sla: String(base.response_time_sla_seconds),
    forensic_level: base.forensic_level,
    notify_targets: JSON.stringify(base.notify_targets || []),
    compliance_report: String(base.compliance_report),
    record_threshold: String(base.record_threshold),
  }
}

export default function PolicyBuilderPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [baselines, setBaselines] = useState<Baseline[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [expandedBaseline, setExpandedBaseline] = useState<string | null>(null)
  const [applying, setApplying] = useState(false)

  // ODP Editor state
  const [editingOdps, setEditingOdps] = useState<Record<string, ODPFormState>>({})
  const [savingOdp, setSavingOdp] = useState<string | null>(null)
  const [odpConflicts, setOdpConflicts] = useState<Record<string, ConflictItem[]>>({})

  // Comparison state
  const [compareType, setCompareType] = useState<string>('AGT-DEL-001')
  const [compareResults, setCompareResults] = useState<Record<string, DryRunResult[]>>({})
  const [compareLoading, setCompareLoading] = useState(false)
  const [showComparison, setShowComparison] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/policy-builder/templates`).then((r) => r.json()),
      fetch(`${API_BASE}/policy-builder/nist-baseline`).then((r) => r.json()),
      fetchConflicts().catch(() => {}),
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
      // Refresh baselines + conflicts after apply
      await Promise.all([fetchBaselines(), fetchConflicts()])
    } catch {
      alert('Failed to apply template')
    }
    setApplying(false)
  }

  const fetchBaselines = async () => {
    try {
      const res = await fetch(`${API_BASE}/policy-builder/nist-baseline`, {
        credentials: 'include',
      })
      const data = await res.json()
      setBaselines(data.data?.items || [])
    } catch {}
  }

  const fetchConflicts = async () => {
    try {
      const res = await fetch(`${API_BASE}/policy-builder/conflicts`, {
        credentials: 'include',
      })
      if (!res.ok) return
      const data: Record<string, ConflictItem[]> = await res.json()
      setOdpConflicts(data)
    } catch {
      setOdpConflicts({})
    }
  }

  const saveOdp = async (incidentType: string) => {
    const form = editingOdps[incidentType]
    if (!form) return
    setSavingOdp(incidentType)
    try {
      const payload = {
        severity_threshold: form.severity_threshold,
        auto_contain_enabled: form.auto_contain_enabled === 'true',
        escalation_contacts: form.escalation_contacts,
        response_time_sla_seconds: parseInt(form.response_time_sla, 10) || 0,
        forensic_level: form.forensic_level,
        notify_targets: form.notify_targets,
        compliance_report: form.compliance_report === 'true',
        record_threshold: parseInt(form.record_threshold, 10) || 0,
      }
      const res = await fetch(`${API_BASE}/policy-builder/odps/${incidentType}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      })
      if (res.ok) {
        await Promise.all([fetchBaselines(), fetchConflicts()])
        alert('ODP saved successfully')
      } else {
        const err = await res.json().catch(() => ({}))
        alert(err.detail || 'Failed to save ODP')
      }
    } catch {
      alert('Failed to save ODP')
    }
    setSavingOdp(null)
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
                  <OdpEditorForm
                    base={base}
                    conflicts={odpConflicts[base.incident_type] || []}
                    value={editingOdps[base.incident_type]}
                    onChange={(form) =>
                      setEditingOdps((prev) => ({
                        ...prev,
                        [base.incident_type]: form,
                      }))
                    }
                    onSave={() => saveOdp(base.incident_type)}
                    onReset={() =>
                      setEditingOdps((prev) => ({
                        ...prev,
                        [base.incident_type]: baselineToForm(base),
                      }))
                    }
                    saving={savingOdp === base.incident_type}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function OdpEditorForm({
  base,
  conflicts,
  value,
  onChange,
  onSave,
  onReset,
  saving,
}: {
  base: Baseline
  conflicts: ConflictItem[]
  value?: ODPFormState
  onChange: (form: ODPFormState) => void
  onSave: () => void
  onReset: () => void
  saving: boolean
}) {
  const form = value ?? baselineToForm(base)
  const hasConflicts = conflicts.length > 0

  const update = (patch: Partial<ODPFormState>) => {
    onChange({ ...form, ...patch })
  }

  return (
    <div className="mt-4 space-y-4">
      {hasConflicts && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-sm font-semibold text-red-700">
              {conflicts.length} Conflict{conflicts.length > 1 ? 's' : ''}
            </span>
          </div>
          <ul className="space-y-1">
            {conflicts.map((c, i) => (
              <li key={i} className="text-xs text-red-700">
                <strong>{c.conflict_type}:</strong> {c.message}
                {c.actual_value !== undefined && (
                  <span className="text-red-500 ml-1">(got: {c.actual_value})</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Severity Threshold */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Severity Threshold
          </label>
          <select
            value={form.severity_threshold}
            onChange={(e) => update({ severity_threshold: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="critical">CRITICAL</option>
            <option value="high">HIGH</option>
            <option value="medium">MEDIUM</option>
            <option value="low">LOW</option>
          </select>
        </div>

        {/* Auto Contain */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Auto Contain
          </label>
          <select
            value={form.auto_contain_enabled}
            onChange={(e) => update({ auto_contain_enabled: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="true">Enabled</option>
            <option value="false">Disabled</option>
          </select>
        </div>

        {/* Response SLA */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Response SLA (seconds)
          </label>
          <input
            type="number"
            min={0}
            value={form.response_time_sla}
            onChange={(e) => update({ response_time_sla: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Forensic Level */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Forensic Level
          </label>
          <select
            value={form.forensic_level}
            onChange={(e) => update({ forensic_level: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="full">FULL</option>
            <option value="standard">STANDARD</option>
            <option value="basic">BASIC</option>
            <option value="none">NONE</option>
          </select>
        </div>

        {/* Compliance Report */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Compliance Report
          </label>
          <select
            value={form.compliance_report}
            onChange={(e) => update({ compliance_report: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="true">Required</option>
            <option value="false">Optional</option>
          </select>
        </div>

        {/* Record Threshold */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Record Threshold
          </label>
          <input
            type="number"
            min={0}
            value={form.record_threshold}
            onChange={(e) => update({ record_threshold: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Escalation Contacts */}
        <div className="lg:col-span-2">
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Escalation Contacts (JSON array)
          </label>
          <input
            type="text"
            value={form.escalation_contacts}
            onChange={(e) => update({ escalation_contacts: e.target.value })}
            placeholder='["security@company.com"]'
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Notify Targets */}
        <div className="lg:col-span-2">
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Notify Targets (JSON array)
          </label>
          <input
            type="text"
            value={form.notify_targets}
            onChange={(e) => update({ notify_targets: e.target.value })}
            placeholder='["pagerduty"]'
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onSave}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          <Save className="w-3.5 h-3.5" />
          {saving ? 'Saving...' : 'Save ODPs'}
        </button>
        <button
          onClick={onReset}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset to Baseline
        </button>
      </div>
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
