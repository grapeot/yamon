import { useEffect, useState } from 'react'

// Define types inline to avoid import issues
export interface SystemMetrics {
  cpu_percent: number
  cpu_per_core: number[]
  cpu_count: number
  cpu_groups?: CpuGroup[]
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
  cpu_temp_c: number | null
  gpu_temp_c: number | null
}

export interface CpuGroup {
  type: string
  label: string
  count: number
  percent: number
}

interface HistoryData {
  cpu_groups: Record<string, (number | null)[]>
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
  cpu_temp_c: (number | null)[]
  gpu_temp_c: (number | null)[]
}

const emptyHistory: HistoryData = {
  cpu_groups: {},
  cpu_percent: [], cpu_p_percent: [], cpu_e_percent: [], memory_percent: [], memory_used: [],
  network_sent_rate: [], network_recv_rate: [], cpu_power: [], gpu_power: [],
  ane_power: [], system_power: [], gpu_usage: [],
  cpu_temp_c: [], gpu_temp_c: [],
}

export function useWebSocket() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [history, setHistory] = useState<HistoryData>(emptyHistory)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    // 确定 WebSocket URL
    // 在开发环境中，Vite proxy 会将 /ws 转发到后端
    // 在生产环境中，使用相同的 host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/metrics`
    let disposed = false
    let retryTimer: number | undefined
    let retryAttempt = 0
    let ws: WebSocket | null = null

    function connect() {
      if (disposed) return
      const connection = new WebSocket(wsUrl)
      ws = connection

      connection.onopen = () => {
        if (disposed) return
        retryAttempt = 0
        setConnected(true)
      }

      connection.onmessage = (event) => {
        if (disposed) return
        const data = JSON.parse(event.data) as SystemMetrics
        setMetrics(data)
        setHistory((prev) => ({
          cpu_groups: Object.fromEntries((data.cpu_groups ?? []).map(group => [
            group.type, [...(prev.cpu_groups[group.type] ?? prev.cpu_percent.map(() => null)), group.percent].slice(-120),
          ])),
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
          cpu_temp_c: [...prev.cpu_temp_c, data.cpu_temp_c].slice(-120),
          gpu_temp_c: [...prev.gpu_temp_c, data.gpu_temp_c].slice(-120),
        }))
      }

      connection.onerror = (error) => {
        if (disposed) return
        console.error('WebSocket error:', error)
        connection.close()
      }

      connection.onclose = () => {
        if (disposed) return
        setConnected(false)
        const delay = Math.min(1000 * 2 ** retryAttempt, 10000)
        retryAttempt = Math.min(retryAttempt + 1, 4)
        retryTimer = window.setTimeout(connect, delay)
      }
    }

    connect()

    return () => {
      disposed = true
      window.clearTimeout(retryTimer)
      ws?.close()
    }
  }, [])

  return { metrics, history, connected }
}
