import { useEffect, useRef, useCallback } from 'react'

// Derive WS URL from the page's own host so it works on any device/domain.
const WS_BASE = typeof window !== 'undefined'
  ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
  : 'ws://localhost:8000'

/**
 * useWebSocket — connects to the backend /ws endpoint and calls onMessage
 * with each parsed JSON event. Auto-reconnects on disconnect.
 *
 * @param {function} onMessage  - called with parsed JSON object on each message
 * @param {boolean}  enabled    - set false to disable (e.g. during SSR)
 */
export default function useWebSocket(onMessage, enabled = true) {
  const wsRef = useRef(null)
  const timerRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!enabled || typeof window === 'undefined') return
    try {
      const ws = new WebSocket(`${WS_BASE}/ws`)
      wsRef.current = ws

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          onMessageRef.current?.(data)
        } catch (_) {}
      }

      ws.onclose = () => {
        // Reconnect after 3 seconds
        timerRef.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch (_) {
      timerRef.current = setTimeout(connect, 5000)
    }
  }, [enabled])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(timerRef.current)
      wsRef.current?.close()
    }
  }, [connect])
}
