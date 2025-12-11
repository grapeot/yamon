import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface CpuChartProps {
  cpuPercent: number
  cpuPerCore: number[]
  history: number[]
  cpuCount: number
}

export function CpuChart({ cpuPercent, cpuPerCore, history, cpuCount }: CpuChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const resizeHandler = () => {
      chartInstance.current?.resize()
    }
    window.addEventListener('resize', resizeHandler)

    return () => {
      window.removeEventListener('resize', resizeHandler)
      chartInstance.current?.dispose()
    }
  }, [])

  useEffect(() => {
    if (!chartInstance.current) return

    const updatedHistory = [...history, cpuPercent].slice(-120)
    
    // 检测 P 核和 E 核
    // Apple Silicon 通常：M1/M2/M3: 4P+4E, M1 Pro/Max: 8P+2E, M2 Pro/Max: 8P+4E, M3 Pro: 6P+6E, M3 Max: 12P+4E
    // 简单策略：假设前一半是 P 核，后一半是 E 核（对于大多数情况）
    // 或者根据核心数量推断
    let pCoreCount = 0
    let eCoreCount = 0
    
    if (cpuCount === 8) {
      // M1/M2/M3: 4P + 4E
      pCoreCount = 4
      eCoreCount = 4
    } else if (cpuCount === 10) {
      // M1 Pro/Max: 8P + 2E
      pCoreCount = 8
      eCoreCount = 2
    } else if (cpuCount === 12) {
      // M2 Pro/Max: 8P + 4E 或 M3 Pro: 6P + 6E
      // 默认假设 8P + 4E
      pCoreCount = 8
      eCoreCount = 4
    } else if (cpuCount === 16) {
      // M3 Max: 12P + 4E
      pCoreCount = 12
      eCoreCount = 4
    } else {
      // 默认：前一半是 P 核
      pCoreCount = Math.floor(cpuCount / 2)
      eCoreCount = cpuCount - pCoreCount
    }

    // 计算 P 核和 E 核的平均使用率
    const pCores = cpuPerCore.slice(0, pCoreCount)
    const eCores = cpuPerCore.slice(pCoreCount)
    
    const pCoreAvg = pCores.length > 0 ? pCores.reduce((sum, val) => sum + val, 0) / pCores.length : 0
    const eCoreAvg = eCores.length > 0 ? eCores.reduce((sum, val) => sum + val, 0) / eCores.length : 0
    
    // 计算总使用率用于分配历史数据
    const totalCoreUsage = pCoreAvg * pCoreCount + eCoreAvg * eCoreCount
    const pRatio = totalCoreUsage > 0 ? (pCoreAvg * pCoreCount) / totalCoreUsage : 0
    const eRatio = totalCoreUsage > 0 ? (eCoreAvg * eCoreCount) / totalCoreUsage : 0

    chartInstance.current.setOption({
      title: {
        text: `CPU Usage: ${cpuPercent.toFixed(1)}% (P: ${pCoreAvg.toFixed(1)}%, E: ${eCoreAvg.toFixed(1)}%)`,
        left: 'center',
        top: 10,
        textStyle: { fontSize: 14, color: '#fff' },
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = ''
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${param.value.toFixed(1)}%<br/>`
          })
          return result
        },
      },
      legend: {
        data: [`P-Cores (${pCoreCount})`, `E-Cores (${eCoreCount})`],
        top: '10%',
        textStyle: { color: '#aaa' },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '40%',
        containLabel: true,
      },
      animation: false,
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: updatedHistory.map((_, i) => i),
        axisLabel: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        name: 'Usage %',
        nameTextStyle: { color: '#aaa' },
        axisLabel: { color: '#aaa' },
        splitLine: { lineStyle: { color: '#333' } },
      },
      series: [
        {
          name: `P-Cores (${pCoreCount})`,
          type: 'line',
          stack: 'CPU',
          smooth: false,
          showSymbol: false,
          areaStyle: { 
            opacity: 0.6,
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#ee6666' },
                { offset: 1, color: '#ee666680' },
              ],
            },
          },
          lineStyle: { color: '#ee6666', width: 2 },
          itemStyle: { color: '#ee6666' },
          data: updatedHistory.map((total) => pRatio * total),
        },
        {
          name: `E-Cores (${eCoreCount})`,
          type: 'line',
          stack: 'CPU',
          smooth: false,
          showSymbol: false,
          areaStyle: { 
            opacity: 0.6,
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#73c0de' },
                { offset: 1, color: '#73c0de80' },
              ],
            },
          },
          lineStyle: { color: '#73c0de', width: 2 },
          itemStyle: { color: '#73c0de' },
          data: updatedHistory.map((total) => eRatio * total),
        },
      ],
    })
  }, [cpuPercent, cpuPerCore, history, cpuCount])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '200px' }}></div>
    </div>
  )
}
