import { useState, useEffect } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { CpuChart } from './components/CpuChart'
import { MemoryChart } from './components/MemoryChart'
import { NetworkChart } from './components/NetworkChart'
import { PowerChart } from './components/PowerChart'
import { GpuChart } from './components/GpuChart'
import { AneChart } from './components/AneChart'
import './App.css'

// Define types inline to avoid import issues
interface SystemMetrics {
  cpu_percent: number
  cpu_per_core: number[]
  cpu_count: number
  cpu_p_percent: number
  cpu_e_percent: number
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

interface HistoryData {
  cpu_percent: number[]
  cpu_p_percent: number[]
  cpu_e_percent: number[]
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

function App() {
  const { metrics, connected } = useWebSocket()
  // Type assertion for metrics
  const typedMetrics = metrics as SystemMetrics | null
  const [history, setHistory] = useState<HistoryData>({
    cpu_percent: [],
    cpu_p_percent: [],
    cpu_e_percent: [],
    memory_percent: [],
    network_sent_rate: [],
    network_recv_rate: [],
    cpu_power: [],
    gpu_power: [],
    ane_power: [],
    system_power: [],
    gpu_usage: [],
    ane_usage: [],
  })

  // 更新历史数据
  useEffect(() => {
    if (!typedMetrics) return

    setHistory((prev) => ({
      cpu_percent: [...prev.cpu_percent, typedMetrics.cpu_percent].slice(-120),
      cpu_p_percent: [...prev.cpu_p_percent, typedMetrics.cpu_p_percent].slice(-120),
      cpu_e_percent: [...prev.cpu_e_percent, typedMetrics.cpu_e_percent].slice(-120),
      memory_percent: [...prev.memory_percent, typedMetrics.memory_percent].slice(-120),
      network_sent_rate: [...prev.network_sent_rate, typedMetrics.network_sent_rate].slice(-120),
      network_recv_rate: [...prev.network_recv_rate, typedMetrics.network_recv_rate].slice(-120),
      cpu_power: [...prev.cpu_power, typedMetrics.cpu_power || 0].slice(-120),
      gpu_power: [...prev.gpu_power, typedMetrics.gpu_power || 0].slice(-120),
      ane_power: [...prev.ane_power, typedMetrics.ane_power || 0].slice(-120),
      system_power: [...prev.system_power, typedMetrics.system_power || 0].slice(-120),
      gpu_usage: [...prev.gpu_usage, typedMetrics.gpu_usage || 0].slice(-120),
      ane_usage: [...prev.ane_usage, typedMetrics.ane_usage || 0].slice(-120),
    }))
  }, [typedMetrics])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Yamon - Mac System Monitor</h1>
        <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </div>
      </header>

      <main className="dashboard">
        {!typedMetrics ? (
          <div className="loading">Connecting to server...</div>
        ) : (
          <div className="metrics-grid">
            <div className="metric-section">
              <CpuChart
                cpuPercent={typedMetrics.cpu_percent}
                cpuPerCore={typedMetrics.cpu_per_core}
                cpuPPercent={typedMetrics.cpu_p_percent}
                cpuEPercent={typedMetrics.cpu_e_percent}
                cpuPHistory={history.cpu_p_percent}
                cpuEHistory={history.cpu_e_percent}
                cpuCount={typedMetrics.cpu_count}
              />
            </div>

            <div className="metric-section">
              <MemoryChart
                memoryPercent={typedMetrics.memory_percent}
                memoryUsed={typedMetrics.memory_used}
                memoryTotal={typedMetrics.memory_total}
                history={history.memory_percent}
              />
            </div>

            <div className="metric-section">
              <GpuChart
                gpuUsage={typedMetrics.gpu_usage}
                gpuFreqMhz={typedMetrics.gpu_freq_mhz}
                history={history.gpu_usage}
              />
            </div>

            <div className="metric-section">
              <AneChart
                aneUsage={typedMetrics.ane_usage}
                history={history.ane_usage}
              />
            </div>

            <div className="metric-section">
              <NetworkChart
                sentRate={typedMetrics.network_sent_rate}
                recvRate={typedMetrics.network_recv_rate}
                sentHistory={history.network_sent_rate}
                recvHistory={history.network_recv_rate}
              />
            </div>

            <div className="metric-section">
              <PowerChart
                cpuPower={typedMetrics.cpu_power}
                gpuPower={typedMetrics.gpu_power}
                anePower={typedMetrics.ane_power}
                systemPower={typedMetrics.system_power}
                cpuHistory={history.cpu_power}
                gpuHistory={history.gpu_power}
                aneHistory={history.ane_power}
                systemHistory={history.system_power}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
