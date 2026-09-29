import { useWebSocket } from './hooks/useWebSocket'
import { CpuChart } from './components/CpuChart'
import { MemoryChart } from './components/MemoryChart'
import { NetworkChart } from './components/NetworkChart'
import { PowerChart } from './components/PowerChart'
import { GpuChart } from './components/GpuChart'
import { SummaryStrip } from './components/SummaryStrip'
import { TemperatureChart } from './components/TemperatureChart'
import './App.css'

function App() {
  const { metrics: typedMetrics, history, connected } = useWebSocket()

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
                cpuPPercent={typedMetrics.cpu_p_percent}
                cpuEPercent={typedMetrics.cpu_e_percent}
                pcpuFreqMhz={typedMetrics.pcpu_freq_mhz ?? null}
                ecpuFreqMhz={typedMetrics.ecpu_freq_mhz ?? null}
                cpuPHistory={history.cpu_p_percent}
                cpuEHistory={history.cpu_e_percent}
                cpuPCount={typedMetrics.cpu_p_count}
                cpuECount={typedMetrics.cpu_e_count}
              />
            </div>

            <div className="metric-section">
              <MemoryChart
                memoryPercent={typedMetrics.memory_percent}
                memoryTotal={typedMetrics.memory_total}
                history={history.memory_percent}
                usedHistory={history.memory_used}
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

            <div className="metric-section">
              <TemperatureChart
                cpuTempC={typedMetrics.cpu_temp_c}
                gpuTempC={typedMetrics.gpu_temp_c}
                cpuHistory={history.cpu_temp_c}
                gpuHistory={history.gpu_temp_c}
              />
            </div>
          </div>
        )}
      </main>
      <footer className="app-footer">
        <SummaryStrip />
      </footer>
    </div>
  )
}

export default App
