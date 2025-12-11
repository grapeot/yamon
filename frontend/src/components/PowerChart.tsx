import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface PowerChartProps {
  cpuPower: number | null
  gpuPower: number | null
  anePower: number | null
  systemPower: number | null
  cpuHistory: number[]
  gpuHistory: number[]
  aneHistory: number[]
  systemHistory: number[]
}

export function PowerChart({
  cpuPower,
  gpuPower,
  anePower,
  systemPower,
  cpuHistory,
  gpuHistory,
  aneHistory,
  systemHistory,
}: PowerChartProps) {
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

    const updatedCpuHistory = [...cpuHistory, cpuPower || 0].slice(-120)
    const updatedGpuHistory = [...gpuHistory, gpuPower || 0].slice(-120)
    const updatedAneHistory = [...aneHistory, anePower || 0].slice(-120)
    const updatedSystemHistory = [...systemHistory, systemPower || 0].slice(-120)

    // Calculate "Other" power (System - Components)
    // If System < Components (e.g. measurement lag), floor at 0
    const otherHistory = updatedSystemHistory.map((sys, i) => {
      const components = updatedCpuHistory[i] + updatedGpuHistory[i] + updatedAneHistory[i]
      return Math.max(0, sys - components)
    })

    chartInstance.current.setOption({
      title: {
        show: false, // Hide ECharts title, we'll use HTML text instead for selectability
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = ''
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${param.value.toFixed(2)}W<br/>`
          })
          const total = params.reduce((sum: number, p: any) => sum + p.value, 0)
          result += `<b>Total: ${total.toFixed(2)}W</b>`
          return result
        },
      },
      legend: {
        data: ['CPU', 'GPU', 'ANE', 'Other'],
        top: '25%',
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
        data: updatedCpuHistory.map((_, i) => i),
        axisLabel: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        name: 'Power (W)',
        nameTextStyle: { color: '#aaa', fontSize: 12 },
        axisLabel: { color: '#aaa', fontSize: 12 },
        splitLine: { lineStyle: { color: '#333' } },
      },
      series: [
        {
          name: 'CPU',
          type: 'line',
          stack: 'Power',
          smooth: false,
          showSymbol: false,
          areaStyle: { opacity: 0.7 },
          lineStyle: { color: '#ee6666' },
          itemStyle: { color: '#ee6666' },
          data: updatedCpuHistory,
        },
        {
          name: 'GPU',
          type: 'line',
          stack: 'Power',
          smooth: false,
          showSymbol: false,
          areaStyle: { opacity: 0.7 },
          lineStyle: { color: '#73c0de' },
          itemStyle: { color: '#73c0de' },
          data: updatedGpuHistory,
        },
        {
          name: 'ANE',
          type: 'line',
          stack: 'Power',
          smooth: false,
          showSymbol: false,
          areaStyle: { opacity: 0.7 },
          lineStyle: { color: '#3ba272' },
          itemStyle: { color: '#3ba272' },
          data: updatedAneHistory,
        },
        {
          name: 'Other',
          type: 'line',
          stack: 'Power',
          smooth: false,
          showSymbol: false,
          areaStyle: { opacity: 0.5 },
          lineStyle: { color: '#91cc75' },
          itemStyle: { color: '#91cc75' },
          data: otherHistory,
        },
      ],
    })
  }, [cpuPower, gpuPower, anePower, systemPower, cpuHistory, gpuHistory, aneHistory, systemHistory])

  const titleText = `Power: CPU: ${(cpuPower || 0).toFixed(2)}W, GPU: ${(gpuPower || 0).toFixed(2)}W, ANE: ${(anePower || 0).toFixed(2)}W, System: ${systemPower !== null ? systemPower.toFixed(2) + 'W' : 'N/A'}`

  return (
    <div className="chart-container">
      <div style={{ 
        textAlign: 'center', 
        fontSize: '18px', 
        color: '#fff', 
        marginBottom: '10px',
        userSelect: 'text',
        WebkitUserSelect: 'text',
        cursor: 'text'
      }}>
        {titleText}
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
    </div>
  )
}

