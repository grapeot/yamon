import { useEffect, useState, useRef } from 'react'

// Define types inline to avoid import issues
export interface SystemMetrics {
  cpu_percent: number
  cpu_per_core: number[]
  cpu_count: number
  cpu_p_percent: number
  cpu_e_percent: number
  pcpu_freq_mhz: number | null
  ecpu_freq_mhz: number | null
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
    // 在开发环境中，Vite proxy 会将 /ws 转发到后端
    // 在生产环境中，使用相同的 host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = import.meta.env.DEV
      ? `${protocol}//${window.location.host}/ws/metrics`  // 开发环境：通过 Vite proxy
      : `${protocol}//${window.location.host}/ws/metrics`  // 生产环境：同源

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
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
