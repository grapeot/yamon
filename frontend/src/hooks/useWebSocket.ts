import { useEffect, useState, useRef } from 'react'

// Define types inline to avoid import issues
export interface SystemMetrics {
  cpu_percent: number
  cpu_per_core: number[]
  cpu_count: number
  cpu_p_percent: number | null
  cpu_e_percent: number | null
  cpu_p_count: number | null
  cpu_e_count: number | null
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
  cpu_temp_c: number | null
  gpu_temp_c: number | null
}

interface HistoryData {
  cpu_percent: number[]
  cpu_p_percent: (number | null)[]
  cpu_e_percent: (number | null)[]
  memory_percent: number[]
  memory_used: number[]
  network_sent_rate: number[]
  network_recv_rate: number[]
  cpu_power: (number | null)[]
  gpu_power: (number | null)[]
  ane_power: (number | null)[]
  system_power: (number | null)[]
  gpu_usage: (number | null)[]
  ane_usage: (number | null)[]
  cpu_temp_c: (number | null)[]
  gpu_temp_c: (number | null)[]
}

const emptyHistory: HistoryData = {
  cpu_percent: [], cpu_p_percent: [], cpu_e_percent: [], memory_percent: [], memory_used: [],
  network_sent_rate: [], network_recv_rate: [], cpu_power: [], gpu_power: [],
  ane_power: [], system_power: [], gpu_usage: [], ane_usage: [],
  cpu_temp_c: [], gpu_temp_c: [],
}

export function useWebSocket() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [history, setHistory] = useState<HistoryData>(emptyHistory)
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
      setHistory((prev) => ({
        cpu_percent: [...prev.cpu_percent, data.cpu_percent].slice(-120),
        cpu_p_percent: [...prev.cpu_p_percent, data.cpu_p_percent].slice(-120),
        cpu_e_percent: [...prev.cpu_e_percent, data.cpu_e_percent].slice(-120),
        memory_percent: [...prev.memory_percent, data.memory_percent].slice(-120),
        memory_used: [...prev.memory_used, data.memory_used].slice(-120),
        network_sent_rate: [...prev.network_sent_rate, data.network_sent_rate].slice(-120),
        network_recv_rate: [...prev.network_recv_rate, data.network_recv_rate].slice(-120),
        cpu_power: [...prev.cpu_power, data.cpu_power].slice(-120),
        gpu_power: [...prev.gpu_power, data.gpu_power].slice(-120),
        ane_power: [...prev.ane_power, data.ane_power].slice(-120),
        system_power: [...prev.system_power, data.system_power].slice(-120),
        gpu_usage: [...prev.gpu_usage, data.gpu_usage].slice(-120),
        ane_usage: [...prev.ane_usage, data.ane_usage].slice(-120),
        cpu_temp_c: [...prev.cpu_temp_c, data.cpu_temp_c].slice(-120),
        gpu_temp_c: [...prev.gpu_temp_c, data.gpu_temp_c].slice(-120),
      }))
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

  return { metrics, history, connected }
}
