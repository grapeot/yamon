import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface CpuChartProps {
  cpuPercent: number
  cpuPPercent: number | null
  cpuEPercent: number | null
  cpuPCount: number | null
  cpuECount: number | null
  pcpuFreqMhz: number | null
  ecpuFreqMhz: number | null
  cpuPHistory: (number | null)[]
  cpuEHistory: (number | null)[]
}

export function CpuChart({ cpuPercent, cpuPPercent, cpuEPercent, cpuPCount, cpuECount,
  pcpuFreqMhz, ecpuFreqMhz, cpuPHistory, cpuEHistory }: CpuChartProps) {
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
    const pLabel = `P-Cores (${cpuPCount ?? '—'})`
    const eLabel = `E-Cores (${cpuECount ?? '—'})`
    chartInstance.current.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', valueFormatter: (value: unknown) =>
        typeof value === 'number' ? `${value.toFixed(1)}%` : '—' },
      legend: { data: [pLabel, eLabel], top: '18%', textStyle: { color: '#aaa', fontSize: 14 } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '35%', containLabel: true },
      animation: false,
      xAxis: { type: 'category', boundaryGap: false, data: cpuPHistory.map((_, i) => i),
        axisLabel: { show: false } },
      yAxis: { type: 'value', min: 0, max: 100, name: 'Usage %',
        nameTextStyle: { color: '#aaa', fontSize: 12 },
        axisLabel: { color: '#aaa', fontSize: 12 },
        splitLine: { lineStyle: { color: '#333' } } },
      series: [
        { name: pLabel, type: 'line', stack: 'CPU', showSymbol: false,
          areaStyle: { opacity: 0.6 }, lineStyle: { color: '#ee6666', width: 2 },
          itemStyle: { color: '#ee6666' }, data: cpuPHistory },
        { name: eLabel, type: 'line', stack: 'CPU', showSymbol: false,
          areaStyle: { opacity: 0.6 }, lineStyle: { color: '#73c0de', width: 2 },
          itemStyle: { color: '#73c0de' }, data: cpuEHistory },
      ],
    })
  }, [cpuPHistory, cpuEHistory, cpuPCount, cpuECount])

  const groups = cpuPPercent === null || cpuEPercent === null
    ? 'P: —, E: —'
    : `P: ${cpuPPercent.toFixed(1)}%, E: ${cpuEPercent.toFixed(1)}%`
  const frequency = [
    pcpuFreqMhz == null ? null : `P: ${pcpuFreqMhz.toFixed(0)} MHz`,
    ecpuFreqMhz == null ? null : `E: ${ecpuFreqMhz.toFixed(0)} MHz`,
  ].filter(Boolean).join(', ')
  const title = `CPU Usage: ${cpuPercent.toFixed(1)}% (${groups})${frequency ? ` [${frequency}]` : ''}`

  return <div className="chart-container">
    <div style={{ textAlign: 'center', fontSize: '18px', color: '#fff', marginBottom: '10px',
      userSelect: 'text', WebkitUserSelect: 'text', cursor: 'text' }}>{title}</div>
    <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
  </div>
}
