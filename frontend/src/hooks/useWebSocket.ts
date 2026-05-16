import { useEffect, useRef, useState, useCallback } from 'react'
import { getWsUrl, getSoundAlerts } from '../utils/config'
import { getToken } from '../utils/api'

interface WebSocketMessage {
  event_type: string
  [key: string]: any
}

const MAX_RECONNECT_ATTEMPTS = 10
const INITIAL_RECONNECT_DELAY_MS = 1000
const MAX_RECONNECT_DELAY_MS = 30000

export function useWebSocket() {
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isMountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!isMountedRef.current) return

    const token = getToken()
    let WS_URL = getWsUrl()
    if (token) {
      const sep = WS_URL.includes('?') ? '&' : '?'
      WS_URL += `${sep}token=${encodeURIComponent(token)}`
    }

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      if (!isMountedRef.current) return
      setConnected(true)
      reconnectAttemptsRef.current = 0
      ws.send(JSON.stringify({ action: 'subscribe', filters: {} }))
    }

    ws.onclose = () => {
      if (!isMountedRef.current) return
      setConnected(false)
      wsRef.current = null

      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(
          INITIAL_RECONNECT_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current),
          MAX_RECONNECT_DELAY_MS
        )
        reconnectAttemptsRef.current += 1
        reconnectTimerRef.current = setTimeout(() => {
          connect()
        }, delay)
      }
    }

    ws.onmessage = (event) => {
      if (!isMountedRef.current) return
      try {
        const data = JSON.parse(event.data) as WebSocketMessage
        setMessages((prev) => [data, ...prev].slice(0, 50))

        if (
          data.event_type === 'incident_detected' &&
          data.severity === 'critical' &&
          getSoundAlerts()
        ) {
          try {
            const audio = new Audio('/alert.mp3')
            audio.volume = 0.5
            audio.play().catch(() => {})
          } catch {
            // ignore audio errors
          }
        }
      } catch {
        // ignore malformed messages
      }
    }

    ws.onerror = () => {
      if (!isMountedRef.current) return
      setConnected(false)
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    connect()

    return () => {
      isMountedRef.current = false
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const send = useCallback((message: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  return { connected, messages, send }
}
