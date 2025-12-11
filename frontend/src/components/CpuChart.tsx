import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface CpuChartProps {
  cpuPercent: number
  cpuPerCore: number[]
  cpuPPercent: number
  cpuEPercent: number
  cpuPercentHistory: number[]
  cpuPHistory: number[]
  cpuEHistory: number[]
  cpuCount: number
}

export function CpuChart({ cpuPercent, cpuPerCore, cpuPPercent, cpuEPercent, cpuPercentHistory, cpuPHistory, cpuEHistory, cpuCount }: CpuChartProps) {
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

    // 使用实际记录的 P 核和 E 核历史数据（这些是占整体算力的比例，0-100%）
    const updatedPHistory = [...cpuPHistory, cpuPPercent].slice(-120)
    const updatedEHistory = [...cpuEHistory, cpuEPercent].slice(-120)
    // 总CPU使用率历史数据
    const updatedTotalHistory = [...cpuPercentHistory, cpuPercent].slice(-120)
    
    // 计算P核和E核对总CPU使用率的实际贡献
    // P核实际贡献 = 总使用率 * (P占整体算力的比例 / 100)
    // E核实际贡献 = 总使用率 * (E占整体算力的比例 / 100)
    const pActualHistory = updatedTotalHistory.map((total, i) => {
      const pRatio = updatedPHistory[i] / 100.0
      return total * pRatio
    })
    const eActualHistory = updatedTotalHistory.map((total, i) => {
      const eRatio = updatedEHistory[i] / 100.0
      return total * eRatio
    })

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

    chartInstance.current.setOption({
      title: {
        text: `CPU Usage: ${cpuPercent.toFixed(1)}% (P占${cpuPPercent.toFixed(1)}%, E占${cpuEPercent.toFixed(1)}%)`,
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
        top: '25%',
        textStyle: { color: '#aaa', fontSize: 14 },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '30%',
        containLabel: true,
      },
      animation: false,
      xAxis: {
        type: 'category',
        boundaryGap: false,
          data: pActualHistory.map((_, i: number) => i),
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
          data: pActualHistory,
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
          data: eActualHistory,
        },
      ],
    })
  }, [cpuPercent, cpuPerCore, cpuPPercent, cpuEPercent, cpuPercentHistory, cpuPHistory, cpuEHistory, cpuCount])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
    </div>
  )
}
