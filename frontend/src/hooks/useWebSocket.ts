import { useEffect, useRef, useState, useCallback } from 'react'
import { getWsUrl, getSoundAlerts } from '../utils/config'

interface WebSocketMessage {
  event_type: string
  [key: string]: any
}

export function useWebSocket() {
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const WS_URL = getWsUrl()
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      // Subscribe to all incidents
      ws.send(JSON.stringify({ action: 'subscribe', filters: {} }))
    }

    ws.onclose = () => {
      setConnected(false)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage
        setMessages((prev) => [data, ...prev].slice(0, 50))

        // Sound alert for CRITICAL incidents
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
      setConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [])

  const send = useCallback((message: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  return { connected, messages, send }
}
