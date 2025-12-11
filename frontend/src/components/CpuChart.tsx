import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface CpuChartProps {
  cpuPercent: number
  cpuPerCore: number[]
  cpuPPercent: number
  cpuEPercent: number
  pcpuFreqMhz: number | null
  ecpuFreqMhz: number | null
  cpuPHistory: number[]
  cpuEHistory: number[]
  cpuCount: number
}

export function CpuChart({ cpuPercent, cpuPerCore, cpuPPercent, cpuEPercent, pcpuFreqMhz, ecpuFreqMhz, cpuPHistory, cpuEHistory, cpuCount }: CpuChartProps) {
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

    // 使用实际记录的 P 核和 E 核历史数据（这些是对总CPU使用率的贡献百分比）
    // cpuPPercent 和 cpuEPercent 已经是贡献百分比，直接使用即可
    const updatedPHistory = [...cpuPHistory, cpuPPercent].slice(-120)
    const updatedEHistory = [...cpuEHistory, cpuEPercent].slice(-120)

    // 检测 P 核和 E 核数量（用于显示）
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

    // Build title with frequencies if available
    // cpuPercent should equal cpuPPercent + cpuEPercent (both are frequency-scaled)
    // Ensure consistency: use cpuPPercent + cpuEPercent if they don't match cpuPercent
    const calculatedTotal = cpuPPercent + cpuEPercent
    const displayTotal = Math.abs(cpuPercent - calculatedTotal) < 0.1 ? cpuPercent : calculatedTotal
    
    let titleText = `CPU Usage: ${displayTotal.toFixed(1)}% (P: ${cpuPPercent.toFixed(1)}%, E: ${cpuEPercent.toFixed(1)}%)`
    if (pcpuFreqMhz !== null || ecpuFreqMhz !== null) {
      const freqParts: string[] = []
      if (pcpuFreqMhz !== null) {
        freqParts.push(`P: ${pcpuFreqMhz.toFixed(0)} MHz`)
      }
      if (ecpuFreqMhz !== null) {
        freqParts.push(`E: ${ecpuFreqMhz.toFixed(0)} MHz`)
      }
      if (freqParts.length > 0) {
        titleText += ` [${freqParts.join(', ')}]`
      }
    }

    chartInstance.current.setOption({
      title: {
        text: titleText,
        left: 'center',
        top: 10,
        textStyle: { fontSize: 18, color: '#fff' },
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
        top: '18%',
        textStyle: { color: '#aaa', fontSize: 14 },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '35%',
        containLabel: true,
      },
      animation: false,
      xAxis: {
        type: 'category',
        boundaryGap: false,
          data: updatedPHistory.map((_, i: number) => i),
        axisLabel: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        name: 'Usage %',
        nameTextStyle: { color: '#aaa', fontSize: 12 },
        axisLabel: { color: '#aaa', fontSize: 12 },
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
          data: updatedPHistory,
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
          data: updatedEHistory,
        },
      ],
    })
  }, [cpuPercent, cpuPerCore, cpuPPercent, cpuEPercent, pcpuFreqMhz, ecpuFreqMhz, cpuPHistory, cpuEHistory, cpuCount])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
    </div>
  )
}
