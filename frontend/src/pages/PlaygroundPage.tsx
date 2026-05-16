import { useEffect, useRef, useState } from 'react'
import { apiFetch, API_BASE, getToken } from '../utils/api'
import { getWsUrl } from '../utils/config'
import {
  Play,
  Square,
  Plus,
  Trash2,
  Bot,
  BrainCircuit,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Zap,
  ChevronDown,
  ChevronUp,
  Code,
  Copy,
  Check,
  Terminal,
  Lock,
} from 'lucide-react'

interface Provider {
  name: string
  display_name: string
  description: string
  requires_api_key: boolean
  default_model: string
  configurable_fields: string[]
}

interface Template {
  id: string
  name: string
  description: string
  agent_count: number
}

interface PlaygroundEvent {
  event_id: string
  event_type: string
  agent_id?: string
  agent_name?: string
  payload: any
  timestamp: number
}

interface Session {
  id: string
  name: string
  status: string
  provider_name: string
  industry_template?: string
  created_at: string
}

export default function PlaygroundPage() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSession, setActiveSession] = useState<Session | null>(null)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [events, setEvents] = useState<PlaygroundEvent[]>([])
  const [wsConnected, setWsConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  // Provider config
  const [selectedProvider, setSelectedProvider] = useState('openai')
  const [providerConfig, setProviderConfig] = useState<Record<string, string>>({
    model: 'gpt-4o-mini',
    api_key: '',
    base_url: '',
    project_id: '',
    location: '',
  })
  const [providerValid, setProviderValid] = useState<boolean | null>(null)
  const [providerValidated, setProviderValidated] = useState(false)
  const [availableModels, setAvailableModels] = useState<{id: string; name: string}[]>([])
  const [isCustomModel, setIsCustomModel] = useState(false)

  // Session builder
  const [showBuilder, setShowBuilder] = useState(false)
  const [sessionName, setSessionName] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('')

  // Human-in-the-loop approval
  const [awaitingApproval, setAwaitingApproval] = useState<null | {
    session_id: string
    agent_name: string
    action: string
    verdict: string
  }>(null)

  const eventsEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const activeSessionIdRef = useRef<string | null>(null)

  // Keep ref in sync with state so WebSocket handler sees current value
  useEffect(() => {
    activeSessionIdRef.current = activeSessionId
  }, [activeSessionId])

  const _api = async (path: string, opts?: RequestInit) => {
    const res = await apiFetch(`${API_BASE}${path}`, opts)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || err.message || `HTTP ${res.status}`)
    }
    return res.json()
  }

  useEffect(() => {
    loadProviders()
    loadTemplates()
    loadSessions()
  }, [])

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  // WebSocket for live events
  useEffect(() => {
    let wsUrl = getWsUrl()
    const token = getToken()
    if (token) {
      const sep = wsUrl.includes('?') ? '&' : '?'
      wsUrl += `${sep}token=${encodeURIComponent(token)}`
    }
    const ws = new WebSocket(wsUrl)
    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data)
        if (data.type === 'playground_event') {
          // Only append if it belongs to the currently viewed session
          if (activeSessionIdRef.current && data.session_id !== activeSessionIdRef.current) return
          const normalized: PlaygroundEvent = {
            event_id: data.event_id,
            event_type: data.event_type,
            agent_id: data.agent_id,
            agent_name: data.agent_name,
            payload: data.payload,
            timestamp: typeof data.timestamp === 'number' ? data.timestamp : new Date(data.timestamp).getTime() / 1000,
          }
          setEvents((prev) => [...prev, normalized])
        }
      } catch {}
    }
    wsRef.current = ws
    return () => ws.close()
  }, [])

  // Load historical events when active session changes
  useEffect(() => {
    if (!activeSessionId) {
      setEvents([])
      return
    }
    loadSessionEvents(activeSessionId)
  }, [activeSessionId])

  const loadSessionEvents = async (sessionId: string) => {
    try {
      const res = await _api(`/playground/sessions/${sessionId}/events?page_size=200`)
      const items = res.data?.items || []
      setEvents(items.map((item: any) => ({
        event_id: item.event_id,
        event_type: item.event_type,
        agent_id: item.agent_id,
        agent_name: item.agent_name,
        payload: item.payload,
        timestamp: new Date(item.timestamp).getTime() / 1000,
      })))
    } catch (e: any) {
      console.error('Failed to load session events:', e)
    }
  }

  // Poll session status for human-in-the-loop approval
  useEffect(() => {
    if (!activeSessionId) return
    const interval = setInterval(async () => {
      try {
        const res = await _api(`/playground/sessions/${activeSessionId}/status`)
        if (res.data?.awaiting_human_approval) {
          setAwaitingApproval({
            session_id: activeSessionId,
            ...res.data.approval_data,
          })
        } else {
          setAwaitingApproval(null)
        }
      } catch (e: any) {
        console.error('Polling session status failed:', e)
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [activeSessionId])

  const loadProviders = async () => {
    try {
      const res = await _api('/playground/providers')
      setProviders(res.data?.providers || [])
    } catch (e: any) {
      console.error(e)
    }
  }

  const loadTemplates = async () => {
    try {
      const res = await _api('/playground/templates')
      setTemplates(res.data?.templates || [])
    } catch (e: any) {
      console.error(e)
    }
  }

  const loadSessions = async () => {
    try {
      const res = await _api('/playground/sessions')
      setSessions(res.data?.items || [])
    } catch (e: any) {
      console.error(e)
    }
  }

  const validateProvider = async () => {
    setProviderValid(null)
    setProviderValidated(false)
    setAvailableModels([])
    setIsCustomModel(false)
    setLoading(true)
    try {
      const res = await _api('/playground/providers/validate', {
        method: 'POST',
        body: JSON.stringify({ provider_name: selectedProvider, config: providerConfig }),
      })
      setProviderValid(res.success !== false)
      if (res.success === false) {
        setError(res.message || 'Provider validation failed')
      } else {
        setError('')
        const statusRes = await _api('/playground/provider-validation-status', {
          method: 'POST',
          body: JSON.stringify({ provider_name: selectedProvider, config: providerConfig }),
        })
        setProviderValidated(statusRes.data?.valid === true)
        if (statusRes.data?.valid !== true && statusRes.data?.error) {
          setError(statusRes.data.error)
        }
        const modelsRes = await _api('/playground/providers/models', {
          method: 'POST',
          body: JSON.stringify({ provider_name: selectedProvider, config: providerConfig }),
        })
        const models = modelsRes.data?.models || []
        setAvailableModels(models)
      }
    } catch (e: any) {
      setProviderValid(false)
      setProviderValidated(false)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const createFromTemplate = async () => {
    if (!selectedTemplate || !providerValidated) return
    setLoading(true)
    setError('')
    try {
      const res = await _api('/playground/sessions/from-template', {
        method: 'POST',
        body: JSON.stringify({
          template_id: selectedTemplate,
          provider_name: selectedProvider,
          provider_config: providerConfig,
        }),
      })
      await loadSessions()
      setShowBuilder(false)
      // Auto-start
      const sessionId = res.data?.session_id
      if (sessionId) {
        await _api(`/playground/sessions/${sessionId}/start`, { method: 'POST' })
        await loadSessions()
        const sessRes = await _api(`/playground/sessions/${sessionId}`)
        setActiveSession(sessRes.data)
        setActiveSessionId(sessionId)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const startSession = async (sessionId: string) => {
    setLoading(true)
    try {
      await _api(`/playground/sessions/${sessionId}/start`, { method: 'POST' })
      await loadSessions()
      const sessRes = await _api(`/playground/sessions/${sessionId}`)
      setActiveSession(sessRes.data)
      setActiveSessionId(sessionId)
      setEvents([])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const stopSession = async (sessionId: string) => {
    setLoading(true)
    try {
      await _api(`/playground/sessions/${sessionId}/stop`, { method: 'POST' })
      await loadSessions()
      setActiveSession((prev) => (prev?.id === sessionId ? null : prev))
      if (activeSessionId === sessionId) {
        setActiveSessionId(null)
        setAwaitingApproval(null)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const [deletingId, setDeletingId] = useState<string | null>(null)

  const deleteSession = async (sessionId: string) => {
    if (deletingId === sessionId) {
      // Second click — confirm delete
      setDeletingId(null)
      setLoading(true)
      try {
        await _api(`/playground/sessions/${sessionId}`, { method: 'DELETE' })
        await loadSessions()
        setActiveSession((prev) => (prev?.id === sessionId ? null : prev))
        if (activeSessionId === sessionId) {
          setActiveSessionId(null)
          setAwaitingApproval(null)
        }
        setError('')
      } catch (e: any) {
        const msg = e.message || 'Delete failed'
        setError(msg)
        alert('Delete failed: ' + msg)
      } finally {
        setLoading(false)
      }
    } else {
      // First click — show confirmation state
      setDeletingId(sessionId)
      // Auto-reset after 3 seconds if not clicked again
      setTimeout(() => setDeletingId((prev) => (prev === sessionId ? null : prev)), 3000)
    }
  }

  const handleApprove = async () => {
    if (!awaitingApproval) return
    setLoading(true)
    try {
      await _api(`/playground/sessions/${awaitingApproval.session_id}/approve`, { method: 'POST' })
      setAwaitingApproval(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDeny = async () => {
    if (!awaitingApproval) return
    setLoading(true)
    try {
      await _api(`/playground/sessions/${awaitingApproval.session_id}/deny`, { method: 'POST' })
      setAwaitingApproval(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEscalate = () => {
    if (!awaitingApproval) return
    console.log('Escalating to incident:', awaitingApproval)
    alert(`Escalated: ${awaitingApproval.agent_name} — ${awaitingApproval.action} (${awaitingApproval.verdict})`)
    setAwaitingApproval(null)
  }

  const getEventColor = (type: string) => {
    switch (type) {
      case 'agent_thought':
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200'
      case 'llm_response':
        return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 text-purple-800 dark:text-purple-200'
      case 'action_requested':
        return 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200'
      case 'judge_verdict':
        return 'bg-rose-50 dark:bg-rose-900/20 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200'
      case 'system':
        return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300'
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200'
      default:
        return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
    }
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'agent_thought':
        return <Bot className="w-4 h-4" />
      case 'llm_response':
        return <BrainCircuit className="w-4 h-4" />
      case 'action_requested':
        return <Zap className="w-4 h-4" />
      case 'judge_verdict':
        return <ShieldAlert className="w-4 h-4" />
      case 'error':
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Terminal className="w-4 h-4" />
    }
  }

  const sdkSnippet = `from playbook_sdk import guard, PlaybookClient

client = PlaybookClient(
    endpoint="http://localhost:8001",
    api_key="your-jwt-token"
)

@guard(
    agent_id="MyAgent",
    action_type="customer_support",
    endpoint="http://localhost:8001",
    api_key="your-jwt-token",
    metadata={"severity": "low", "auth_present": True}
)
def process_refund(order_id: str):
    # Your LLM-driven logic here
    return {"status": "refunded"}

# Every call to process_refund() is intercepted
# by the PLAYBOOK Judge Layer before execution.`

  const copySdk = () => {
    navigator.clipboard.writeText(sdkSnippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Agent Simulator Playground</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Configure LLM providers, deploy agent swarms, and watch the Judge Layer intercept actions in real time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
              wsConnected
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
            }`}
          >
            {wsConnected ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" /> Live
              </>
            ) : (
              <>
                <AlertTriangle className="w-3.5 h-3.5" /> Disconnected
              </>
            )}
          </span>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Provider Config */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider mb-4 flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-blue-500" />
          LLM Provider Configuration
          {providerValidated && (
            <CheckCircle2 className="w-4 h-4 text-green-500 ml-1" />
          )}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => {
                const nextProvider = e.target.value
                setSelectedProvider(nextProvider)
                const p = providers.find((x) => x.name === nextProvider)
                setProviderConfig((prev) => ({
                  ...prev,
                  model: p?.default_model || '',
                  api_key: '',
                  ...(nextProvider === 'gemini_adc' && !prev.location ? { location: 'global' } : {}),
                }))
                setProviderValid(null)
                setProviderValidated(false)
                setAvailableModels([])
                setIsCustomModel(false)
              }}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
            >
              {providers.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.display_name}
                </option>
              ))}
            </select>
          </div>
          {selectedProvider === 'gemini_adc' && (
            <>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">GCP Project ID</label>
                <input
                  type="text"
                  value={providerConfig.project_id}
                  onChange={(e) => setProviderConfig((prev) => ({ ...prev, project_id: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                  placeholder="my-gcp-project"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Location</label>
                <input
                  type="text"
                  value={providerConfig.location}
                  onChange={(e) => setProviderConfig((prev) => ({ ...prev, location: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                  placeholder="us-central1"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Base URL</label>
                <input
                  type="text"
                  value={providerConfig.base_url}
                  onChange={(e) => setProviderConfig((prev) => ({ ...prev, base_url: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                  placeholder="https://..."
                />
              </div>
            </>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Model</label>
            {availableModels.length > 0 && !isCustomModel ? (
              <select
                value={providerConfig.model}
                onChange={(e) => {
                  const value = e.target.value
                  if (value === '__custom__') {
                    setIsCustomModel(true)
                  } else {
                    setProviderConfig((prev) => ({ ...prev, model: value }))
                  }
                }}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              >
                {availableModels.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
                <option value="__custom__">Custom model</option>
              </select>
            ) : (
              <input
                type="text"
                value={providerConfig.model}
                onChange={(e) => setProviderConfig((prev) => ({ ...prev, model: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                placeholder={providers.find((p) => p.name === selectedProvider)?.default_model || 'model-name'}
              />
            )}
          </div>
          {providers.find((p) => p.name === selectedProvider)?.requires_api_key && (
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <input
                type="password"
                value={providerConfig.api_key}
                onChange={(e) => setProviderConfig((prev) => ({ ...prev, api_key: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                placeholder="sk-..."
              />
            </div>
          )}
          <div className="flex items-end">
            <button
              onClick={validateProvider}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              Test Connection
            </button>
          </div>
        </div>
        {providerValid === true && (
          <p className="mt-2 text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Provider configuration is valid
          </p>
        )}
        {providerValid === false && (
          <p className="mt-2 text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> Provider validation failed
          </p>
        )}
      </div>

      {/* Session Builder */}
      <div className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 ${!providerValidated ? 'opacity-60 pointer-events-none relative' : ''}`}>
        {!providerValidated && (
          <div className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 px-4 py-2 rounded-lg shadow-sm">
              <Lock className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Please validate a provider first</span>
            </div>
          </div>
        )}
        <button
          onClick={() => setShowBuilder((s) => !s)}
          disabled={!providerValidated}
          className="w-full flex items-center justify-between text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider disabled:opacity-50"
        >
          <span className="flex items-center gap-2">
            <Plus className="w-4 h-4 text-blue-500" />
            New Simulation Session
          </span>
          {showBuilder ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showBuilder && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Session Name</label>
                <input
                  type="text"
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                  placeholder="Healthcare Swarm Test"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Industry Template</label>
                <select
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">-- Custom --</option>
                  {templates.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.agent_count} agents)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedTemplate && (
              <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 text-sm text-blue-800 dark:text-blue-200">
                <strong>Template:</strong> {templates.find((t) => t.id === selectedTemplate)?.name}
                <br />
                {templates.find((t) => t.id === selectedTemplate)?.description}
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                onClick={createFromTemplate}
                disabled={loading || !selectedTemplate || !providerValidated}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Create & Launch
              </button>
              <button
                onClick={() => {
                  setShowBuilder(false)
                  setSelectedTemplate('')
                }}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Active Sessions */}
      {sessions.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider mb-4">
            Sessions
          </h2>
          <div className="space-y-2">
            {sessions.map((sess) => (
              <div
                key={sess.id}
                className={`flex items-center justify-between rounded-lg border px-4 py-3 transition-colors ${
                  activeSession?.id === sess.id
                    ? 'border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-900/10'
                    : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Bot className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{sess.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {sess.provider_name} · {sess.industry_template || 'custom'} ·{' '}
                      <span
                        className={`font-medium ${
                          sess.status === 'running'
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-gray-500 dark:text-gray-400'
                        }`}
                      >
                        {sess.status}
                      </span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {sess.status === 'running' ? (
                    <button
                      onClick={() => stopSession(sess.id)}
                      disabled={loading}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-amber-100 hover:bg-amber-200 dark:bg-amber-900/30 dark:hover:bg-amber-900/50 text-amber-700 dark:text-amber-300 px-3 py-1.5 text-xs font-medium transition-colors"
                    >
                      <Square className="w-3.5 h-3.5" /> Stop
                    </button>
                  ) : (
                    <button
                      onClick={() => startSession(sess.id)}
                      disabled={loading}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:hover:bg-green-900/50 text-green-700 dark:text-green-300 px-3 py-1.5 text-xs font-medium transition-colors"
                    >
                      <Play className="w-3.5 h-3.5" /> Start
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setActiveSession(sess)
                      setActiveSessionId(sess.id)
                    }}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    View
                  </button>
                  <button
                    onClick={() => deleteSession(sess.id)}
                    disabled={loading}
                    className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                      deletingId === sess.id
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400'
                    }`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    {deletingId === sess.id ? 'Confirm?' : ''}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Event Feed + SDK Snippet */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Events */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 flex flex-col h-[600px]">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-blue-500" />
            Live Event Feed
            {activeSession && (
              <span className="text-xs font-normal text-gray-500 dark:text-gray-400 ml-2">
                — {activeSession.name}
              </span>
            )}
          </h2>

          {/* Human-in-the-loop approval banner */}
          {awaitingApproval && (
            <div className="mb-4 rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                <h3 className="text-sm font-bold text-amber-800 dark:text-amber-200">Human Approval Required</h3>
              </div>
              <div className="text-sm text-amber-800 dark:text-amber-200 space-y-1 mb-3">
                <p>
                  <span className="font-medium">Agent:</span>{' '}
                  {awaitingApproval.agent_name} wants to execute:{" "}
                  <span className="font-mono font-semibold">{awaitingApproval.action}</span>
                </p>
                <p>
                  <span className="font-medium">Judge Verdict:</span>{' '}
                  <span className="font-bold">{awaitingApproval.verdict}</span>
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleApprove}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                </button>
                <button
                  onClick={handleDeny}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <Square className="w-3.5 h-3.5" /> Deny
                </button>
                <button
                  onClick={handleEscalate}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <ShieldAlert className="w-3.5 h-3.5" /> Escalate
                </button>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {events.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
                <Bot className="w-10 h-10 mb-2 opacity-50" />
                <p className="text-sm">Start a session to see live events</p>
              </div>
            )}
            {events.map((ev, idx) => (
              <div
                key={`${ev.event_id}-${idx}`}
                className={`rounded-lg border p-3 text-sm ${getEventColor(ev.event_type)}`}
              >
                <div className="flex items-start gap-2">
                  <div className="mt-0.5">{getEventIcon(ev.event_type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold capitalize">{ev.event_type.replace(/_/g, ' ')}</span>
                      {ev.agent_name && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-white/60 dark:bg-black/20 font-medium">
                          {ev.agent_name}
                        </span>
                      )}
                    </div>
                    <div className="text-xs opacity-90 space-y-0.5">
                      {ev.payload?.situation && <p className="italic">&ldquo;{ev.payload.situation}&rdquo;</p>}
                      {ev.payload?.reasoning && <p>{ev.payload.reasoning}</p>}
                      {ev.payload?.action && (
                        <p>
                          Action: <span className="font-mono font-medium">{ev.payload.action}</span>
                          {ev.payload.is_malicious && (
                            <span className="ml-2 text-red-600 dark:text-red-400 font-bold">[MALICIOUS]</span>
                          )}
                        </p>
                      )}
                      {ev.payload?.verdict && (
                        <p>
                          Verdict:{" "}
                          <span
                            className={`font-bold ${
                              ev.payload.verdict === 'ALLOW'
                                ? 'text-green-700 dark:text-green-400'
                                : ev.payload.verdict === 'QUARANTINE'
                                ? 'text-amber-700 dark:text-amber-400'
                                : 'text-red-700 dark:text-red-400'
                            }`}
                          >
                            {ev.payload.verdict}
                          </span>
                          {ev.payload.latency_ms !== undefined && (
                            <span className="ml-2 text-gray-500 dark:text-gray-400">
                              ({ev.payload.latency_ms}ms)
                            </span>
                          )}
                        </p>
                      )}
                      {ev.payload?.rationale && <p className="text-gray-500 dark:text-gray-400">{ev.payload.rationale}</p>}
                      {ev.payload?.message && <p>{ev.payload.message}</p>}
                      {ev.payload?.error && <p className="text-red-600 dark:text-red-400">{ev.payload.error}</p>}
                      {ev.payload?.mismatch && (
                        <p className="text-red-600 dark:text-red-400 font-bold">
                          ⚠ MISMATCH — Judge overrode LLM!
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div ref={eventsEndRef} />
          </div>
        </div>

        {/* SDK Integration */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Code className="w-4 h-4 text-blue-500" />
            SDK Integration
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
            Wrap any agent action with the <code className="font-mono text-blue-600 dark:text-blue-400">@guard</code>{" "}
            decorator. The Judge Layer intercepts every call before execution.
          </p>
          <div className="relative">
            <pre className="rounded-lg bg-gray-900 text-gray-100 p-3 text-xs overflow-x-auto font-mono leading-relaxed">
              {sdkSnippet}
            </pre>
            <button
              onClick={copySdk}
              className="absolute top-2 right-2 p-1.5 rounded-md bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
              title="Copy to clipboard"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
          <div className="mt-4 space-y-2">
            <h3 className="text-xs font-semibold text-gray-700 dark:text-gray-300">Supported Providers</h3>
            <div className="flex flex-wrap gap-2">
              {['OpenAI', 'Gemini', 'Ollama', 'Azure', 'Claude'].map((name) => (
                <span
                  key={name}
                  className="px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-400 font-medium"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-4 space-y-2">
            <h3 className="text-xs font-semibold text-gray-700 dark:text-gray-300">Framework Middleware</h3>
            <div className="flex flex-wrap gap-2">
              {['LangChain', 'CrewAI', 'LlamaIndex', 'AutoGen'].map((name) => (
                <span
                  key={name}
                  className="px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-400 font-medium"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
