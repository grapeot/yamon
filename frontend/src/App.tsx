import { useState, useEffect } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { MetricCard } from './components/MetricCard'
import './App.css'

// Define types inline to avoid import issues
interface SystemMetrics {
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

interface HistoryData {
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

function App() {
  const { metrics, connected } = useWebSocket()
  // Type assertion for metrics
  const typedMetrics = metrics as SystemMetrics | null
  const [history, setHistory] = useState<HistoryData>({
    cpu_percent: [],
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
      cpu_percent: [...prev.cpu_percent, typedMetrics.cpu_percent].slice(-60),
      memory_percent: [...prev.memory_percent, typedMetrics.memory_percent].slice(-60),
      network_sent_rate: [...prev.network_sent_rate, typedMetrics.network_sent_rate].slice(-60),
      network_recv_rate: [...prev.network_recv_rate, typedMetrics.network_recv_rate].slice(-60),
      cpu_power: [...prev.cpu_power, typedMetrics.cpu_power || 0].slice(-60),
      gpu_power: [...prev.gpu_power, typedMetrics.gpu_power || 0].slice(-60),
      ane_power: [...prev.ane_power, typedMetrics.ane_power || 0].slice(-60),
      system_power: [...prev.system_power, typedMetrics.system_power || 0].slice(-60),
      gpu_usage: [...prev.gpu_usage, typedMetrics.gpu_usage || 0].slice(-60),
      ane_usage: [...prev.ane_usage, typedMetrics.ane_usage || 0].slice(-60),
    }))
  }, [typedMetrics])

  const formatBytes = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let size = bytes
    let unitIndex = 0
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`
  }

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
              <h2>CPU</h2>
              <MetricCard 
                title="CPU Usage" 
                value={typedMetrics.cpu_percent.toFixed(1)} 
                unit="%" 
              />
              <div className="cpu-cores">
                <h3>Per Core ({typedMetrics.cpu_count} cores)</h3>
                <div className="cores-grid">
                  {typedMetrics.cpu_per_core.map((percent, idx) => (
                    <div key={idx} className="core-item">
                      <div className="core-label">Core {idx}</div>
                      <div className="core-value">{percent.toFixed(1)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="metric-section">
              <h2>Memory</h2>
              <MetricCard 
                title="Memory Usage" 
                value={typedMetrics.memory_percent.toFixed(1)} 
                unit="%" 
              />
              <div className="memory-details">
                <div>Used: {formatBytes(typedMetrics.memory_used)}</div>
                <div>Total: {formatBytes(typedMetrics.memory_total)}</div>
                <div>Available: {formatBytes(typedMetrics.memory_available)}</div>
              </div>
            </div>

            <div className="metric-section">
              <h2>Network</h2>
              <MetricCard 
                title="Upload" 
                value={formatBytes(typedMetrics.network_sent_rate)} 
                unit="/s" 
              />
              <MetricCard 
                title="Download" 
                value={formatBytes(typedMetrics.network_recv_rate)} 
                unit="/s" 
              />
            </div>

            <div className="metric-section">
              <h2>Power</h2>
              <MetricCard 
                title="CPU Power" 
                value={typedMetrics.cpu_power?.toFixed(2) || null} 
                unit="W" 
              />
              <MetricCard 
                title="GPU Power" 
                value={typedMetrics.gpu_power?.toFixed(2) || null} 
                unit="W" 
              />
              <MetricCard 
                title="ANE Power" 
                value={typedMetrics.ane_power?.toFixed(2) || null} 
                unit="W" 
              />
              <MetricCard 
                title="System Power" 
                value={typedMetrics.system_power?.toFixed(2) || null} 
                unit="W" 
              />
            </div>

            <div className="metric-section">
              <h2>GPU</h2>
              <MetricCard 
                title="GPU Usage" 
                value={typedMetrics.gpu_usage?.toFixed(1) || null} 
                unit="%" 
              />
              {typedMetrics.gpu_freq_mhz && (
                <MetricCard 
                  title="GPU Frequency" 
                  value={typedMetrics.gpu_freq_mhz.toFixed(0)} 
                  unit=" MHz" 
                />
              )}
            </div>

            <div className="metric-section">
              <h2>ANE</h2>
              <MetricCard 
                title="ANE Usage" 
                value={typedMetrics.ane_usage?.toFixed(1) || null} 
                unit="%" 
              />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
