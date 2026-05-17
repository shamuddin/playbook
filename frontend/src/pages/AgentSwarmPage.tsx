import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, API_BASE } from '../utils/api'
import { getWsUrl } from '../utils/config'
import {
  Play,
  Square,
  Bot,
  Shield,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Zap,
  ChevronDown,
  ChevronUp,
  Clock,
  Activity,
  Wifi,
  WifiOff,
  Lock,
  ExternalLink,
  Terminal,
  Eye,
  EyeOff,
  Flame,
  Skull,
  Target,
} from 'lucide-react'

interface Scenario {
  id: string
  name: string
  description: string
  agents: number
  tasks: number
  incident_type: string
}

interface SwarmEvent {
  event_type: string
  agent_id: string
  message: string
  verdict?: string
  latency_ms?: number
  timestamp?: number
}

interface SwarmStatus {
  running: boolean
  total_events: number
  allowed: number
  blocked: number
  agent_count: number
}

function formatEventType(raw: string): string {
  const labels: Record<string, string> = {
    agent_registered: 'Agent Registered',
    agent_thought: 'Agent Reasoning',
    agent_action: 'Action Executed',
    judge_verdict: 'Judge Verdict',
    judge_error: 'Judge Error',
    incident_created: 'Incident Created',
    swarm_complete: 'Complete',
    swarm_stopped: 'Stopped',
  }
  return labels[raw] || raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

const SCENARIOS: Scenario[] = [
  {
    id: 'fx-swap',
    name: 'FX Swap Unauthorized Trade',
    description:
      'Step Finance Trader v3 attempts a $40M FX swap beyond its $5M authorization limit through an unvetted broker.',
    agents: 1,
    tasks: 2,
    incident_type: 'AGT-FIN-002',
  },
  {
    id: 'data-exfil',
    name: 'Data Exfiltration',
    description:
      'Data Analyst agent is asked to export customer PII (emails and SSNs) to an unauthorized external destination.',
    agents: 1,
    tasks: 2,
    incident_type: 'AGT-EXT-005',
  },
  {
    id: 'prompt-injection',
    name: 'Prompt Injection Attack',
    description:
      'Customer Support Bot receives a jailbreak prompt attempting to make it reveal system prompts and internal credentials.',
    agents: 1,
    tasks: 2,
    incident_type: 'AGT-INJ-006',
  },
  {
    id: 'full-swarm',
    name: 'Full 3-Agent Swarm',
    description:
      'All three agents run concurrently: FX Trader, Data Analyst, and Support Bot. Each executes one normal and one malicious action.',
    agents: 3,
    tasks: 6,
    incident_type: 'AGT-FIN-002, AGT-EXT-005, AGT-INJ-006',
  },
]

export default function AgentSwarmPage() {
  const navigate = useNavigate()
  const [scenarios] = useState<Scenario[]>(SCENARIOS)
  const [selectedScenario, setSelectedScenario] = useState<string>('full-swarm')
  const REAL_PROJECT_ID = 'project-1fd13dba-5264-4c78-a5c'
  const maskProjectId = (id: string) => {
    if (!id || id.length < 12) return id
    return id.slice(0, 8) + '****-****-****-' + id.slice(-3)
  }

  const [gcpProjectId, setGcpProjectId] = useState(REAL_PROJECT_ID)
  const [showProjectId, setShowProjectId] = useState(false)
  const [gcpRegion, setGcpRegion] = useState('global')
  const [selectedModel, setSelectedModel] = useState('gemini-3.1-flash-lite')
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const [connectionMessage, setConnectionMessage] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [events, setEvents] = useState<SwarmEvent[]>([])
  const [status, setStatus] = useState<SwarmStatus | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showEventFeed, setShowEventFeed] = useState(true)
  const [backendConnected, setBackendConnected] = useState(false)
  const [misbehaviorMode, setMisbehaviorMode] = useState(false)
  const [pulseIndex, setPulseIndex] = useState<number | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const eventsEndRef = useRef<HTMLDivElement>(null)

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await apiFetch(`${API_BASE}/health`)
        setBackendConnected(res.ok)
      } catch {
        setBackendConnected(false)
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [])

  // WebSocket connection
  useEffect(() => {
    const wsUrl = getWsUrl()
    if (!wsUrl) return

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
      // Authenticate
      const token = localStorage.getItem('playbook_token')
      if (token) {
        ws.send(JSON.stringify({ type: 'auth', token }))
      }
    }

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data)
        if (data.event_type === 'swarm_incident_created') {
          setEvents((prev) => [
            ...prev,
            {
              event_type: formatEventType('incident_created'),
              agent_id: data.agent_id,
              message: `Incident ${data.incident_id} created`,
              verdict: data.verdict,
              timestamp: Date.now(),
            },
          ])
        } else if (data.event_type?.startsWith('swarm_')) {
          const baseType = data.event_type.replace('swarm_', '')
          setEvents((prev) => [
            ...prev,
            {
              event_type: formatEventType(baseType),
              agent_id: data.agent_id,
              message: data.message,
              verdict: data.verdict,
              latency_ms: data.latency_ms,
              timestamp: Date.now(),
            },
          ])
        }
      } catch {
        // ignore
      }
    }

    ws.onclose = () => setWsConnected(false)
    ws.onerror = () => setWsConnected(false)

    return () => {
      ws.close()
    }
  }, [])

  // Auto-scroll events and pulse new incidents
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    if (events.length > 0) {
      const latest = events[events.length - 1]
      if (latest.event_type === 'Incident Created') {
        setPulseIndex(events.length - 1)
        const timer = setTimeout(() => setPulseIndex(null), 2500)
        return () => clearTimeout(timer)
      }
    }
  }, [events])

  // Poll status while running
  useEffect(() => {
    if (!running || !sessionId) return

    const poll = async () => {
      try {
        const res = await apiFetch(`${API_BASE}/swarm/${sessionId}/status`)
        if (res.ok) {
          const data = await res.json()
          setStatus(data.data)
          if (!data.data?.running) {
            setRunning(false)
          }
        }
      } catch {
        // ignore
      }
    }

    poll()
    pollRef.current = setInterval(poll, 2000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [running, sessionId])

  const testConnection = async () => {
    if (!gcpProjectId) {
      setConnectionStatus('error')
      setConnectionMessage('Enter a GCP Project ID first')
      return
    }
    setConnectionStatus('testing')
    setConnectionMessage('')

    try {
      const res = await apiFetch(`${API_BASE}/swarm/test-connection`, {
        method: 'POST',
        body: JSON.stringify({
          gcp_project_id: gcpProjectId,
          gcp_region: gcpRegion,
          model: selectedModel,
        }),
      })

      const data = await res.json()
      if (data.success) {
        // Check if backend returned a warning about stub mode
        if (data.data?.warning) {
          setConnectionStatus('success')
          setConnectionMessage('Demo mode — Judge Layer active')
        } else {
          setConnectionStatus('success')
          setConnectionMessage('ADC connected — live LLM calls enabled')
        }
      } else {
        setConnectionStatus('error')
        setConnectionMessage(data.message || 'Connection failed')
      }
    } catch (exc: any) {
      setConnectionStatus('error')
      setConnectionMessage(exc.message || 'Connection test failed')
    }
  }

  const launchSwarm = async () => {
    setLoading(true)
    setError('')
    setEvents([])

    try {
      const res = await apiFetch(`${API_BASE}/swarm/run`, {
        method: 'POST',
        body: JSON.stringify({
          scenario_id: selectedScenario,
          gcp_project_id: gcpProjectId || undefined,
          gcp_region: gcpRegion || undefined,
          model: selectedModel,
          misbehavior_mode: misbehaviorMode,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.message || 'Failed to start swarm')
      }

      const data = await res.json()
      setSessionId(data.data?.session_id)
      setRunning(true)
    } catch (exc: any) {
      setError(exc.message || 'Failed to start swarm')
    } finally {
      setLoading(false)
    }
  }

  const stopSwarm = async () => {
    if (!sessionId) return
    try {
      await apiFetch(`${API_BASE}/swarm/${sessionId}/stop`, { method: 'POST' })
      setRunning(false)
    } catch {
      // ignore
    }
  }

  const getVerdictColor = (verdict?: string, eventType?: string) => {
    if (verdict === 'ALLOW') return 'text-green-600 bg-green-50'
    if (verdict === 'DENY' || verdict === 'BLOCK') return 'text-red-600 bg-red-50'
    if (verdict === 'QUARANTINE') return 'text-orange-600 bg-orange-50'
    if (eventType === 'agent_thought') return 'text-blue-600 bg-blue-50'
    return 'text-gray-600 bg-gray-50'
  }

  const getVerdictIcon = (verdict?: string, eventType?: string) => {
    if (verdict === 'ALLOW') return <ShieldCheck className="w-4 h-4 text-green-600" />
    if (verdict === 'DENY' || verdict === 'BLOCK') return <ShieldAlert className="w-4 h-4 text-red-600" />
    if (verdict === 'QUARANTINE') return <AlertTriangle className="w-4 h-4 text-orange-600" />
    if (eventType === 'agent_thought') return <Bot className="w-4 h-4 text-blue-600" />
    return <Shield className="w-4 h-4 text-gray-500" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bot className="w-7 h-7 text-blue-600" />
            Simulator
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Run real AI agents through PLAYBOOK's deterministic Judge Layer. Watch governance in action.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
              backendConnected
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {backendConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {backendConnected ? 'Backend Connected' : 'Backend Offline'}
          </span>
          <span
            className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
              wsConnected
                ? 'bg-green-100 text-green-700'
                : 'bg-yellow-100 text-yellow-700'
            }`}
          >
            {wsConnected ? <Zap className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
            {wsConnected ? 'Live' : 'Polling'}
          </span>
        </div>
      </div>

      {/* Scenario Selection */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-blue-600" />
            Select Scenario
          </h2>
          {/* Misbehavior Mode Toggle */}
          <button
            onClick={() => setMisbehaviorMode(!misbehaviorMode)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all ${
              misbehaviorMode
                ? 'bg-red-600 text-white shadow-lg shadow-red-500/30 animate-pulse'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Flame className={`w-4 h-4 ${misbehaviorMode ? 'animate-bounce' : ''}`} />
            {misbehaviorMode ? 'Misbehavior Mode ON' : 'Misbehavior Mode'}
          </button>
        </div>

        {misbehaviorMode && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-700">
              <span className="font-semibold">Warning:</span> Agents will attempt malicious actions only.
              All tasks become attacks — expect 100% block rate.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {scenarios.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedScenario(s.id)}
              className={`p-4 rounded-xl border-2 text-left transition-all ${
                selectedScenario === s.id
                  ? misbehaviorMode
                    ? 'border-red-500 bg-red-50 shadow-md shadow-red-500/20'
                    : 'border-blue-500 bg-blue-50'
                  : misbehaviorMode
                  ? 'border-gray-200 hover:border-red-300'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <h3 className="font-semibold text-gray-900 text-sm">{s.name}</h3>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{s.description}</p>
              <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Bot className="w-3 h-3" /> {s.agents}
                </span>
                <span className="flex items-center gap-1">
                  <Activity className="w-3 h-3" /> {s.tasks}
                </span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] ${misbehaviorMode ? 'bg-red-100 text-red-700' : 'bg-gray-100'}`}>
                  {s.incident_type}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Configuration & Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Config */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-blue-600" />
            Configuration
          </h2>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GCP Project ID (ADC)
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={showProjectId ? gcpProjectId : maskProjectId(gcpProjectId)}
                    onChange={(e) => setGcpProjectId(e.target.value)}
                    onFocus={() => {
                      if (!showProjectId) setShowProjectId(true)
                    }}
                    placeholder="e.g. my-project-123"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg bg-white text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowProjectId(!showProjectId)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    title={showProjectId ? 'Hide project ID' : 'Show project ID'}
                  >
                    {showProjectId ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Google Cloud project ID for Vertex AI ADC.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GCP Region
                </label>
                <input
                  type="text"
                  value={gcpRegion}
                  onChange={(e) => setGcpRegion(e.target.value)}
                  placeholder="e.g. global, us-central1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Vertex AI region. Default: global.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gemini Model
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
                >
                  <optgroup label="Gemini 3.1 (Latest)">
                    <option value="gemini-3.1-flash-lite">Gemini 3.1 Flash Lite (fastest)</option>
                    <option value="gemini-3.1-flash">Gemini 3.1 Flash</option>
                    <option value="gemini-3.1-pro">Gemini 3.1 Pro</option>
                  </optgroup>
                  <optgroup label="Gemini 3.0">
                    <option value="gemini-3.0-flash">Gemini 3.0 Flash</option>
                    <option value="gemini-3.0-pro">Gemini 3.0 Pro</option>
                  </optgroup>
                  <optgroup label="Gemini 2.5">
                    <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                    <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                  </optgroup>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Select from Vertex AI Model Garden.
                </p>
              </div>
            </div>

            {/* Test Connection */}
            <div className="flex items-center gap-3">
              <button
                onClick={testConnection}
                disabled={connectionStatus === 'testing'}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  connectionStatus === 'success'
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : connectionStatus === 'error'
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {connectionStatus === 'testing' && <Loader2 className="w-4 h-4 animate-spin" />}
                {connectionStatus === 'success' && <CheckCircle2 className="w-4 h-4" />}
                {connectionStatus === 'error' && <AlertTriangle className="w-4 h-4" />}
                {connectionStatus === 'idle' && <Wifi className="w-4 h-4" />}
                {connectionStatus === 'testing'
                  ? 'Testing...'
                  : connectionStatus === 'success'
                  ? 'Ready'
                  : connectionStatus === 'error'
                  ? 'Failed'
                  : 'Test Connection'}
              </button>
              {connectionMessage && (
                <span
                  className={`text-sm ${
                    connectionStatus === 'success'
                      ? 'text-green-600'
                      : connectionStatus === 'error'
                      ? 'text-red-600'
                      : 'text-gray-500'
                  }`}
                >
                  {connectionMessage}
                </span>
              )}
              {connectionStatus === 'success' && (
                <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">
                  Demo Mode
                </span>
              )}
            </div>

            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-900">
                    How the Swarm Works
                  </p>
                  <ul className="text-xs text-blue-800 mt-2 space-y-1 list-disc list-inside">
                    <li>Each agent action is intercepted by the PLAYBOOK Judge Layer</li>
                    <li>Deterministic rules evaluate ALLOW / DENY / QUARANTINE in &lt; 5ms</li>
                    <li>Blocked actions create real incidents in the database</li>
                    <li>Agents appear in the Agents dashboard via heartbeat</li>
                    <li>Zero LLM calls in the enforcement path</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3 mt-6">
            {!running ? (
              <button
                onClick={launchSwarm}
                disabled={loading || !backendConnected}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                  misbehaviorMode
                    ? 'bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 shadow-lg shadow-red-500/40 animate-pulse'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : misbehaviorMode ? <Skull className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {loading ? 'Launching...' : misbehaviorMode ? 'Launch Swarm Attack' : 'Launch Swarm'}
              </button>
            ) : (
              <button
                onClick={stopSwarm}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold text-white transition-all ${
                  misbehaviorMode
                    ? 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-500/30'
                    : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                <Square className="w-4 h-4" />
                Stop Swarm
              </button>
            )}

            {sessionId && (
              <span className="text-xs text-gray-500 font-mono">
                Session: {sessionId}
              </span>
            )}

            <button
              onClick={() => navigate('/agents')}
              className="ml-auto flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
            >
              View Agents Dashboard
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        {/* Status Panel */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            Live Stats
          </h2>

          {status ? (
            <div className="space-y-4">
              {/* Stat Grid */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <div className="flex items-center justify-center gap-1 text-blue-600 mb-1">
                    <Bot className="w-4 h-4" />
                    <span className="text-xs font-semibold">Agents</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900">{status.agent_count}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
                    <Zap className="w-4 h-4" />
                    <span className="text-xs font-semibold">Events</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900">{status.total_events}</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="flex items-center justify-center gap-1 text-green-600 mb-1">
                    <ShieldCheck className="w-4 h-4" />
                    <span className="text-xs font-semibold">Allowed</span>
                  </div>
                  <div className="text-2xl font-bold text-green-700">{status.allowed}</div>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <div className="flex items-center justify-center gap-1 text-red-600 mb-1">
                    <ShieldAlert className="w-4 h-4" />
                    <span className="text-xs font-semibold">Blocked</span>
                  </div>
                  <div className="text-2xl font-bold text-red-700">{status.blocked}</div>
                </div>
              </div>

              {/* Incidents Counter */}
              <div className={`rounded-lg p-3 flex items-center justify-between ${
                events.filter((e) => e.event_type === 'Incident Created').length > 0
                  ? 'bg-orange-50 border border-orange-200'
                  : 'bg-gray-50'
              }`}>
                <div className="flex items-center gap-2">
                  <Target className={`w-5 h-5 ${
                    events.filter((e) => e.event_type === 'Incident Created').length > 0
                      ? 'text-orange-600'
                      : 'text-gray-400'
                  }`} />
                  <span className="text-sm font-medium text-gray-700">Incidents Generated</span>
                </div>
                <span className={`text-xl font-bold ${
                  events.filter((e) => e.event_type === 'Incident Created').length > 0
                    ? 'text-orange-700'
                    : 'text-gray-400'
                }`}>
                  {events.filter((e) => e.event_type === 'Incident Created').length}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="pt-2">
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all"
                    style={{
                      width: `${
                        status.total_events > 0
                          ? (status.allowed / status.total_events) * 100
                          : 0
                      }%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Allow Rate</span>
                  <span>
                    {status.total_events > 0
                      ? Math.round((status.allowed / status.total_events) * 100)
                      : 0}
                    %
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Launch a swarm to see real-time statistics.
            </p>
          )}
        </div>
      </div>

      {/* Event Feed */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-blue-600" />
            Live Event Feed
            {events.length > 0 && (
              <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                {events.length}
              </span>
            )}
          </h2>
          <button
            onClick={() => setShowEventFeed(!showEventFeed)}
            className="p-1 text-gray-500 hover:text-gray-700"
          >
            {showEventFeed ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {showEventFeed && (
          <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm h-96 overflow-y-auto">
            {events.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                {running ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Waiting for swarm events...
                  </div>
                ) : (
                  'Launch a swarm to see events'
                )}
              </div>
            ) : (
              <div className="space-y-1">
                {events.map((e, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-2 p-2 rounded transition-all duration-500 ${getVerdictColor(e.verdict, e.event_type)} ${
                      pulseIndex === i ? 'ring-2 ring-yellow-400 shadow-lg shadow-yellow-500/20 scale-[1.02]' : ''
                    }`}
                  >
                    <div className="mt-0.5">{getVerdictIcon(e.verdict, e.event_type)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wide opacity-75">
                          {formatEventType(e.event_type)}
                        </span>
                        {e.verdict && (
                          <span className="text-xs font-bold">{e.verdict}</span>
                        )}
                        {e.latency_ms && e.latency_ms > 0 && (
                          <span className="text-xs opacity-75">{e.latency_ms.toFixed(1)}ms</span>
                        )}
                      </div>
                      <p className="text-sm mt-0.5">{e.message}</p>
                      {e.agent_id && (
                        <p className="text-xs opacity-75 mt-0.5">
                          Agent:{' '}
                          <button
                            onClick={() => navigate('/agents')}
                            className="hover:text-blue-600 hover:underline"
                          >
                            {e.agent_id}
                          </button>
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={eventsEndRef} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
