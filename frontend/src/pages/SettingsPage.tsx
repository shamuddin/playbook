import { useEffect, useState, useCallback } from 'react'
import {
  Settings,
  Server,
  Bell,
  SlidersHorizontal,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  Send,
  Radio,
  Volume2,
  VolumeX,
  Globe,
  Wifi,
  Database,
} from 'lucide-react'
import { useLocalStorage } from '../hooks/useLocalStorage'
import { getApiBase } from '../utils/config'

const API_BASE = getApiBase()

interface HealthData {
  status: string
  version: string
  timestamp: string
  components: Record<string, string>
}

interface PublicSettings {
  environment: string
  demo_mode: boolean
  version: string
  notifications: {
    slack: boolean
    email: boolean
    pagerduty: boolean
  }
}

interface TestResult {
  channel: string
  success: boolean
  detail: string
  timestamp: number
}

export default function SettingsPage() {
  // ------------------------------------------------------------------
  // System info
  // ------------------------------------------------------------------
  const [health, setHealth] = useState<HealthData | null>(null)
  const [publicSettings, setPublicSettings] = useState<PublicSettings | null>(null)
  const [loadingHealth, setLoadingHealth] = useState(true)

  const fetchHealth = useCallback(() => {
    setLoadingHealth(true)
    fetch(`${API_BASE}/health`)
      .then((r) => r.json())
      .then((res) => {
        setHealth(res)
        setLoadingHealth(false)
      })
      .catch(() => setLoadingHealth(false))
  }, [])

  const fetchPublicSettings = useCallback(() => {
    fetch(`${API_BASE}/settings/public`)
      .then((r) => r.json())
      .then((res) => {
        if (res.success) setPublicSettings(res.data)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    fetchHealth()
    fetchPublicSettings()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [fetchHealth, fetchPublicSettings])

  // ------------------------------------------------------------------
  // Notification tests
  // ------------------------------------------------------------------
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [testingChannel, setTestingChannel] = useState<string | null>(null)

  const testNotification = useCallback(async (channel: string) => {
    setTestingChannel(channel)
    try {
      const res = await fetch(`${API_BASE}/integrations/notifications/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel,
          message: `Test ${channel} notification from PLAYBOOK`,
          severity: 'high',
          incident_id: 'TEST-001',
        }),
      })
      const data = await res.json()
      const success = data.success && data.data?.success
      const detail = data.data?.detail || data.message || 'No detail'
      setTestResults((prev) => [
        { channel, success, detail, timestamp: Date.now() },
        ...prev.slice(0, 9),
      ])
    } catch (err) {
      setTestResults((prev) => [
        { channel, success: false, detail: String(err), timestamp: Date.now() },
        ...prev.slice(0, 9),
      ])
    } finally {
      setTestingChannel(null)
    }
  }, [])

  // ------------------------------------------------------------------
  // User preferences (localStorage)
  // ------------------------------------------------------------------
  const [apiUrl, setApiUrl] = useLocalStorage('playbook_api_url', 'http://localhost:8000/api/v1')
  const [wsUrl, setWsUrl] = useLocalStorage('playbook_ws_url', 'ws://localhost:8000/ws/incidents')
  const [pageSize, setPageSize] = useLocalStorage('playbook_page_size', 25)
  const [refreshInterval, setRefreshInterval] = useLocalStorage('playbook_refresh_interval', 30)
  const [soundAlerts, setSoundAlerts] = useLocalStorage('playbook_sound_alerts', false)

  const resetPreferences = useCallback(() => {
    setApiUrl('http://localhost:8000/api/v1')
    setWsUrl('ws://localhost:8000/ws/incidents')
    setPageSize(25)
    setRefreshInterval(30)
    setSoundAlerts(false)
  }, [setApiUrl, setWsUrl, setPageSize, setRefreshInterval, setSoundAlerts])

  // ------------------------------------------------------------------
  // Render helpers
  // ------------------------------------------------------------------
  const statusBadge = (ok: boolean) =>
    ok ? (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
        <CheckCircle className="w-3 h-3" /> Healthy
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700 bg-red-50 px-2 py-0.5 rounded-full">
        <XCircle className="w-3 h-3" /> Unhealthy
      </span>
    )

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-3">
        <Settings className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      </div>

      {/* -------------------------------------------------------------- */}
      {/* System Information                                             */}
      {/* -------------------------------------------------------------- */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Server className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">System Information</h2>
          <button
            onClick={fetchHealth}
            className="ml-auto p-1.5 text-gray-400 hover:text-blue-600 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loadingHealth ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loadingHealth && !health ? (
          <div className="flex items-center justify-center h-24">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : health ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Status</p>
              <div className="mt-1">{statusBadge(health.status === 'healthy')}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Version</p>
              <p className="mt-1 text-sm font-medium text-gray-900">{health.version}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Environment</p>
              <p className="mt-1 text-sm font-medium text-gray-900 capitalize">
                {publicSettings?.environment || 'unknown'}
              </p>
              {publicSettings?.demo_mode && (
                <span className="mt-1 inline-block text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
                  Demo Mode
                </span>
              )}
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Last Check</p>
              <p className="mt-1 text-sm font-medium text-gray-900">
                {new Date(health.timestamp).toLocaleTimeString()}
              </p>
            </div>

            {Object.entries(health.components).map(([name, status]) => (
              <div key={name} className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">{name}</p>
                <div className="mt-1">{statusBadge(status === 'healthy')}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-red-600">Unable to reach health endpoint.</p>
        )}
      </section>

      {/* -------------------------------------------------------------- */}
      {/* Notification Integrations                                      */}
      {/* -------------------------------------------------------------- */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Notification Integrations</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {[
            { key: 'slack', label: 'Slack', icon: Send },
            { key: 'email', label: 'Email', icon: Database },
            { key: 'pagerduty', label: 'PagerDuty', icon: Radio },
          ].map(({ key, label, icon: Icon }) => {
            const configured = publicSettings?.notifications?.[key as keyof PublicSettings['notifications']]
            return (
              <div key={key} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-gray-600" />
                    <span className="text-sm font-medium text-gray-900">{label}</span>
                  </div>
                  {configured ? (
                    <span className="text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" /> Configured
                    </span>
                  ) : (
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> Not configured
                    </span>
                  )}
                </div>
                <button
                  onClick={() => testNotification(key)}
                  disabled={testingChannel === key}
                  className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {testingChannel === key ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  Test {label}
                </button>
              </div>
            )
          })}
        </div>

        {testResults.length > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Recent Tests</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {testResults.map((r, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2 p-2 rounded-lg text-sm ${
                    r.success
                      ? 'bg-green-50 text-green-800'
                      : 'bg-red-50 text-red-800'
                  }`}
                >
                  {r.success ? (
                    <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  )}
                  <div>
                    <span className="font-medium capitalize">{r.channel}</span>
                    <span className="text-gray-500 mx-1">·</span>
                    <span>{r.detail}</span>
                    <span className="text-gray-400 ml-2 text-xs">
                      {new Date(r.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* -------------------------------------------------------------- */}
      {/* User Preferences                                               */}
      {/* -------------------------------------------------------------- */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <SlidersHorizontal className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">User Preferences</h2>
          <span className="ml-auto text-xs text-gray-400">Stored in browser</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Globe className="w-4 h-4 inline mr-1 -mt-0.5" />
              API Base URL
            </label>
            <input
              type="url"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="http://localhost:8000/api/v1"
            />
            <p className="mt-1 text-xs text-gray-500">
              Requires page reload to take effect.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Wifi className="w-4 h-4 inline mr-1 -mt-0.5" />
              WebSocket URL
            </label>
            <input
              type="url"
              value={wsUrl}
              onChange={(e) => setWsUrl(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ws://localhost:8000/ws/incidents"
            />
            <p className="mt-1 text-xs text-gray-500">
              Requires page reload to take effect.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Default Page Size
            </label>
            <select
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={10}>10 rows</option>
              <option value={25}>25 rows</option>
              <option value={50}>50 rows</option>
              <option value={100}>100 rows</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Auto-Refresh Interval
            </label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={0}>Off</option>
              <option value={30}>30 seconds</option>
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <div
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  soundAlerts ? 'bg-blue-600' : 'bg-gray-200'
                }`}
                onClick={() => setSoundAlerts(!soundAlerts)}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    soundAlerts ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </div>
              <span className="text-sm font-medium text-gray-700">
                {soundAlerts ? (
                  <Volume2 className="w-4 h-4 inline mr-1 -mt-0.5" />
                ) : (
                  <VolumeX className="w-4 h-4 inline mr-1 -mt-0.5" />
                )}
                Sound Alerts
              </span>
            </label>
            <p className="mt-1 text-xs text-gray-500 ml-14">
              Play a sound when CRITICAL incidents are detected.
            </p>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-xs text-gray-500">
            Preferences are saved automatically to browser local storage.
          </p>
          <button
            onClick={resetPreferences}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Reset to Defaults
          </button>
        </div>
      </section>
    </div>
  )
}
