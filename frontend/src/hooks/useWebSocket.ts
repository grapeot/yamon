import { useEffect, useState, useRef } from 'react'

// Define types inline to avoid import issues
export interface SystemMetrics {
  cpu_percent: number
  cpu_per_core: number[]
  cpu_count: number
  memory_percent: number
  memory_total: number
  memory_used: number
  memory_available: number
  network_sent_rate: number
  network_recv_rate: number
  cpu_power: number | null
  gpu_power: number | null
  ane_power: number | null
  system_power: number | null
  gpu_usage: number | null
  gpu_freq_mhz: number | null
  ane_usage: number | null
}

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
