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
}

export function PowerChart({ 
  cpuPower, 
  gpuPower, 
  anePower, 
  systemPower,
  cpuHistory,
  gpuHistory,
  aneHistory,
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

    const updatedCpuHistory = [...cpuHistory, cpuPower || 0].slice(-60)
    const updatedGpuHistory = [...gpuHistory, gpuPower || 0].slice(-60)
    const updatedAneHistory = [...aneHistory, anePower || 0].slice(-60)

    // 计算总功耗历史（用于堆叠）
    const totalHistory = updatedCpuHistory.map((cpu, i) => 
      cpu + updatedGpuHistory[i] + updatedAneHistory[i]
    )

    const maxPower = Math.max(...totalHistory, systemPower || 0, 1)

    chartInstance.current.setOption({
      title: {
        text: `Power: CPU: ${(cpuPower || 0).toFixed(2)}W, GPU: ${(gpuPower || 0).toFixed(2)}W, ANE: ${(anePower || 0).toFixed(2)}W, System: ${(systemPower || 0).toFixed(2)}W`,
        left: 'center',
        top: 10,
        textStyle: { fontSize: 12, color: '#fff' },
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
        data: ['CPU', 'GPU', 'ANE'],
        top: '10%',
        textStyle: { color: '#aaa' },
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
        nameTextStyle: { color: '#aaa' },
        axisLabel: { color: '#aaa' },
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
      ],
    })
  }, [cpuPower, gpuPower, anePower, systemPower, cpuHistory, gpuHistory, aneHistory])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '200px' }}></div>
    </div>
  )
}

