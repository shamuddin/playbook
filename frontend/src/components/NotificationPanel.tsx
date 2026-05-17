import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, AlertTriangle, Shield, CheckCircle, Clock } from 'lucide-react'
import { getApiBase } from '../utils/config'
import { apiFetch } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'

const API_BASE = getApiBase()

interface Notification {
  id: string
  incident_id: string
  incident_type: string
  severity: string
  message: string
  read: boolean
  created_at: string
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  const loadNotifications = async () => {
    try {
      const res = await apiFetch(`${API_BASE}/incidents?limit=20`)
      if (!res.ok) return
      const data = await res.json()
      const items = data.data || []
      const stored = JSON.parse(localStorage.getItem('playbook_notifications_read') || '[]')

      const notifs: Notification[] = items.map((inc: any) => ({
        id: inc.id,
        incident_id: inc.incident_id,
        incident_type: inc.incident_type,
        severity: inc.severity,
        message: `${inc.incident_type} — ${inc.severity} severity`,
        read: stored.includes(inc.incident_id),
        created_at: inc.created_at,
      }))

      setNotifications(notifs)
      setUnreadCount(notifs.filter((n) => !n.read).length)
    } catch {
      // silently fail — notifications are best-effort
    }
  }

  const addRealtimeNotification = (payload: any) => {
    const stored = JSON.parse(localStorage.getItem('playbook_notifications_read') || '[]')
    const notif: Notification = {
      id: payload.incident_id || payload.id || `rt-${Date.now()}`,
      incident_id: payload.incident_id || '',
      incident_type: payload.notification_type || 'alert',
      severity: payload.severity || 'medium',
      message: payload.message || payload.title || 'New alert',
      read: stored.includes(payload.incident_id),
      created_at: payload.created_at || new Date().toISOString(),
    }
    setNotifications((prev) => {
      const exists = prev.some((n) => n.incident_id === notif.incident_id)
      if (exists) return prev
      return [notif, ...prev].slice(0, 50)
    })
    if (!notif.read) {
      setUnreadCount((c) => Math.min(c + 1, 50))
    }
  }

  const markAllRead = () => {
    const ids = notifications.map((n) => n.incident_id)
    localStorage.setItem('playbook_notifications_read', JSON.stringify(ids))
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
    setUnreadCount(0)
  }

  const markRead = (incidentId: string) => {
    const stored = JSON.parse(localStorage.getItem('playbook_notifications_read') || '[]')
    if (!stored.includes(incidentId)) {
      stored.push(incidentId)
      localStorage.setItem('playbook_notifications_read', JSON.stringify(stored))
    }
    setNotifications((prev) =>
      prev.map((n) => (n.incident_id === incidentId ? { ...n, read: true } : n))
    )
    setUnreadCount((c) => Math.max(0, c - 1))
  }

  return { notifications, unreadCount, loadNotifications, markAllRead, markRead, addRealtimeNotification }
}

export default function NotificationPanel() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const { notifications, unreadCount, loadNotifications, markAllRead, markRead, addRealtimeNotification } =
    useNotifications()
  const { messages } = useWebSocket()

  useEffect(() => {
    loadNotifications()
    const interval = setInterval(loadNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (messages.length === 0) return
    const latest = messages[0]
    if (latest.event_type === 'notification') {
      addRealtimeNotification(latest)
    }
  }, [messages])

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const severityIcon = (severity: string) => {
    if (severity === 'critical') return <AlertTriangle className="w-4 h-4 text-red-500" />
    if (severity === 'high') return <Shield className="w-4 h-4 text-orange-500" />
    return <CheckCircle className="w-4 h-4 text-green-500" />
  }

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => {
          setOpen((o) => !o)
          if (!open) loadNotifications()
        }}
        className="relative p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full px-1">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-900">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-500">
                No recent incidents
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => {
                    markRead(n.incident_id)
                    setOpen(false)
                    navigate(`/incidents/${n.incident_id}`)
                  }}
                  className={`flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors border-b border-gray-50 ${
                    !n.read ? 'bg-blue-50/50' : ''
                  }`}
                >
                  {severityIcon(n.severity)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {n.incident_type}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {n.message}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(n.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!n.read && (
                    <span className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0" />
                  )}
                </div>
              ))
            )}
          </div>

          <div className="px-4 py-2 border-t border-gray-100 bg-gray-50">
            <button
              onClick={() => {
                setOpen(false)
                navigate('/incidents')
              }}
              className="text-xs text-gray-600 hover:text-gray-900 w-full text-center"
            >
              View all incidents
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
