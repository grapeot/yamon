import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import type { CpuGroup } from '../hooks/useWebSocket'

interface CpuChartProps {
  cpuPercent: number
  cpuHistory: number[]
  cpuGroups?: CpuGroup[]
  cpuGroupHistory: Record<string, (number | null)[]>
  cpuPPercent: number | null
  cpuEPercent: number | null
  cpuPCount: number | null
  cpuECount: number | null
  pcpuFreqMhz: number | null
  ecpuFreqMhz: number | null
  cpuPHistory: (number | null)[]
  cpuEHistory: (number | null)[]
}

export function CpuChart({ cpuPercent, cpuHistory, cpuGroups, cpuGroupHistory, cpuPPercent, cpuEPercent, cpuPCount, cpuECount,
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
    const hasGroups = cpuGroups ? cpuGroups.length > 0 : cpuPPercent != null && cpuEPercent != null
    const labels = cpuGroups?.map(group => `${group.label} (${group.count})`) ?? [pLabel, eLabel]
    chartInstance.current.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', valueFormatter: (value: unknown) =>
        typeof value === 'number' ? `${value.toFixed(1)}%` : '—' },
      legend: { data: hasGroups ? labels : ['CPU Usage'], top: '18%', textStyle: { color: '#aaa', fontSize: 14 } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '35%', containLabel: true },
      animation: false,
      xAxis: { type: 'category', boundaryGap: false, data: cpuHistory.map((_, i) => i),
        axisLabel: { show: false } },
      yAxis: { type: 'value', min: 0, max: 100, name: 'Usage %',
        nameTextStyle: { color: '#aaa', fontSize: 12 },
        axisLabel: { color: '#aaa', fontSize: 12 },
        splitLine: { lineStyle: { color: '#333' } } },
      series: hasGroups ? (cpuGroups ? cpuGroups.map((group, index) => ({
        id: group.type, name: labels[index], type: 'line', stack: 'CPU', showSymbol: false,
        areaStyle: { opacity: 0.6 },
        lineStyle: { color: index === 0 ? '#ee6666' : '#73c0de', width: 2 },
        itemStyle: { color: index === 0 ? '#ee6666' : '#73c0de' },
        data: cpuGroupHistory[group.type] ?? [],
      })) : [
        { name: pLabel, type: 'line', stack: 'CPU', showSymbol: false,
          areaStyle: { opacity: 0.6 }, lineStyle: { color: '#ee6666', width: 2 },
          itemStyle: { color: '#ee6666' }, data: cpuPHistory },
        { name: eLabel, type: 'line', stack: 'CPU', showSymbol: false,
          areaStyle: { opacity: 0.6 }, lineStyle: { color: '#73c0de', width: 2 },
          itemStyle: { color: '#73c0de' }, data: cpuEHistory },
      ]) : [
        { name: 'CPU Usage', type: 'line', showSymbol: false,
          areaStyle: { opacity: 0.6 }, lineStyle: { color: '#ee6666', width: 2 },
          itemStyle: { color: '#ee6666' }, data: cpuHistory },
      ],
    }, { replaceMerge: ['series'] })
  }, [cpuHistory, cpuGroups, cpuGroupHistory, cpuPHistory, cpuEHistory, cpuPCount, cpuECount, cpuPPercent, cpuEPercent])

  const groups = cpuGroups?.length
    ? cpuGroups.map(group => `${group.label}: ${group.percent.toFixed(1)}%`).join(', ')
    : cpuPPercent == null || cpuEPercent == null
    ? 'P: —, E: —'
    : `P: ${cpuPPercent.toFixed(1)}%, E: ${cpuEPercent.toFixed(1)}%`
  const frequency = [
    pcpuFreqMhz == null ? null : `${cpuGroups?.find(group => group.type === 'P')?.label ?? 'P'}: ${pcpuFreqMhz.toFixed(0)} MHz`,
    ecpuFreqMhz == null ? null : `E: ${ecpuFreqMhz.toFixed(0)} MHz`,
  ].filter(Boolean).join(', ')
  const title = `CPU Usage: ${cpuPercent.toFixed(1)}% (${groups})${frequency ? ` [${frequency}]` : ''}`

  return <div className="chart-container">
    <div style={{ textAlign: 'center', fontSize: '18px', color: '#fff', marginBottom: '10px',
      userSelect: 'text', WebkitUserSelect: 'text', cursor: 'text' }}>{title}</div>
    <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
  </div>
}
