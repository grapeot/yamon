import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface TemperatureChartProps {
  cpuTempC: number | null
  gpuTempC: number | null
  cpuHistory: (number | null)[]
  gpuHistory: (number | null)[]
}

function degrees(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(1)}°C`
}

export function TemperatureChart({ cpuTempC, gpuTempC, cpuHistory, gpuHistory }: TemperatureChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return
    chartInstance.current = echarts.init(chartRef.current)
    const resizeHandler = () => chartInstance.current?.resize()
    window.addEventListener('resize', resizeHandler)
    return () => {
      window.removeEventListener('resize', resizeHandler)
      chartInstance.current?.dispose()
    }
  }, [])

  useEffect(() => {
    if (!chartInstance.current) return
    chartInstance.current.setOption({
      backgroundColor: 'transparent',
      animation: false,
      tooltip: { trigger: 'axis', valueFormatter: (value: unknown) =>
        typeof value === 'number' ? `${value.toFixed(1)}°C` : '—' },
      legend: { data: ['CPU', 'GPU'], top: '12%', textStyle: { color: '#aaa', fontSize: 14 } },
      grid: { left: '3%', right: '4%', top: '30%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false,
        data: cpuHistory.map((_, index) => index), axisLabel: { show: false } },
      yAxis: { type: 'value', scale: true, name: '°C',
        nameTextStyle: { color: '#aaa', fontSize: 12 },
        axisLabel: { color: '#aaa', fontSize: 12 },
        splitLine: { lineStyle: { color: '#333' } } },
      series: [
        { name: 'CPU', type: 'line', showSymbol: false, connectNulls: false,
          lineStyle: { color: '#ee6666', width: 2 }, itemStyle: { color: '#ee6666' }, data: cpuHistory },
        { name: 'GPU', type: 'line', showSymbol: false, connectNulls: false,
          lineStyle: { color: '#fac858', width: 2 }, itemStyle: { color: '#fac858' }, data: gpuHistory },
      ],
    })
  }, [cpuHistory, gpuHistory])

  return <div className="chart-container">
    <div style={{ textAlign: 'center', fontSize: '18px', color: '#fff', marginBottom: '10px',
      userSelect: 'text', WebkitUserSelect: 'text', cursor: 'text' }}>
      Temperature: CPU {degrees(cpuTempC)} · GPU {degrees(gpuTempC)}
    </div>
    <div ref={chartRef} style={{ width: '100%', height: '270px' }}></div>
  </div>
}
