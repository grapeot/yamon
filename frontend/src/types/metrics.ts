/** System metrics type definitions */

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

export interface HistoryData {
  cpu_percent: number[]
  memory_percent: number[]
  network_sent_rate: number[]
  network_recv_rate: number[]
  cpu_power: number[]
  gpu_power: number[]
  ane_power: number[]
  system_power: number[]
  gpu_usage: number[]
  ane_usage: number[]
}

