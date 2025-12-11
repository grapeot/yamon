import { useEffect, useState, useRef } from 'react'
import type { SystemMetrics } from '../types/metrics'

export function useWebSocket() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // 确定 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.DEV 
      ? 'localhost:8000'  // 开发环境
      : window.location.host  // 生产环境
    const wsUrl = `${protocol}//${host}/ws/metrics`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as SystemMetrics
      setMetrics(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected')
      // 自动重连
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          // 重新连接逻辑可以在这里实现
        }
      }, 3000)
    }

    return () => {
      ws.close()
    }
  }, [])

  return { metrics, connected }
}

