import { useState, useEffect } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import type { SystemMetrics } from './hooks/useWebSocket'
import { MetricCard } from './components/MetricCard'
import './App.css'

// Define HistoryData inline
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
    if (!metrics) return

    setHistory((prev) => ({
      cpu_percent: [...prev.cpu_percent, metrics.cpu_percent].slice(-60),
      memory_percent: [...prev.memory_percent, metrics.memory_percent].slice(-60),
      network_sent_rate: [...prev.network_sent_rate, metrics.network_sent_rate].slice(-60),
      network_recv_rate: [...prev.network_recv_rate, metrics.network_recv_rate].slice(-60),
      cpu_power: [...prev.cpu_power, metrics.cpu_power || 0].slice(-60),
      gpu_power: [...prev.gpu_power, metrics.gpu_power || 0].slice(-60),
      ane_power: [...prev.ane_power, metrics.ane_power || 0].slice(-60),
      system_power: [...prev.system_power, metrics.system_power || 0].slice(-60),
      gpu_usage: [...prev.gpu_usage, metrics.gpu_usage || 0].slice(-60),
      ane_usage: [...prev.ane_usage, metrics.ane_usage || 0].slice(-60),
    }))
  }, [metrics])

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
        {!metrics ? (
          <div className="loading">Connecting to server...</div>
        ) : (
          <div className="metrics-grid">
            <div className="metric-section">
              <h2>CPU</h2>
              <MetricCard 
                title="CPU Usage" 
                value={metrics.cpu_percent.toFixed(1)} 
                unit="%" 
              />
              <div className="cpu-cores">
                <h3>Per Core ({metrics.cpu_count} cores)</h3>
                <div className="cores-grid">
                  {metrics.cpu_per_core.map((percent, idx) => (
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
                value={metrics.memory_percent.toFixed(1)} 
                unit="%" 
              />
              <div className="memory-details">
                <div>Used: {formatBytes(metrics.memory_used)}</div>
                <div>Total: {formatBytes(metrics.memory_total)}</div>
                <div>Available: {formatBytes(metrics.memory_available)}</div>
              </div>
            </div>

            <div className="metric-section">
              <h2>Network</h2>
              <MetricCard 
                title="Upload" 
                value={formatBytes(metrics.network_sent_rate)} 
                unit="/s" 
              />
              <MetricCard 
                title="Download" 
                value={formatBytes(metrics.network_recv_rate)} 
                unit="/s" 
              />
            </div>

            <div className="metric-section">
              <h2>Power</h2>
              <MetricCard 
                title="CPU Power" 
                value={metrics.cpu_power?.toFixed(2) || null} 
                unit="W" 
              />
              <MetricCard 
                title="GPU Power" 
                value={metrics.gpu_power?.toFixed(2) || null} 
                unit="W" 
              />
              <MetricCard 
                title="ANE Power" 
                value={metrics.ane_power?.toFixed(2) || null} 
                unit="W" 
              />
              <MetricCard 
                title="System Power" 
                value={metrics.system_power?.toFixed(2) || null} 
                unit="W" 
              />
            </div>

            <div className="metric-section">
              <h2>GPU</h2>
              <MetricCard 
                title="GPU Usage" 
                value={metrics.gpu_usage?.toFixed(1) || null} 
                unit="%" 
              />
              {metrics.gpu_freq_mhz && (
                <MetricCard 
                  title="GPU Frequency" 
                  value={metrics.gpu_freq_mhz.toFixed(0)} 
                  unit=" MHz" 
                />
              )}
            </div>

            <div className="metric-section">
              <h2>ANE</h2>
              <MetricCard 
                title="ANE Usage" 
                value={metrics.ane_usage?.toFixed(1) || null} 
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
