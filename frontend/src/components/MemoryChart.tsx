import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface MemoryChartProps {
  memoryPercent: number
  memoryTotal: number
  history: number[]
  usedHistory: number[]
}

export function MemoryChart({ memoryPercent, memoryTotal, history, usedHistory }: MemoryChartProps) {
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

    const updatedHistory = history

    chartInstance.current.setOption({
      title: {
        show: false, // Hide ECharts title, we'll use HTML text instead for selectability
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const point = (params as { value: number; dataIndex: number }[])[0]
          const value = point.value
          const usedMB = (usedHistory[point.dataIndex] / 1024 / 1024).toFixed(0)
          const totalMB = (memoryTotal / 1024 / 1024).toFixed(0)
          return `${value.toFixed(1)}%<br/>Used: ${usedMB} MB / ${totalMB} MB`
        },
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
        data: updatedHistory.map((_, i) => i),
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
          name: 'Memory',
          type: 'line',
          smooth: false,
          showSymbol: false,
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#5470c6' },
                { offset: 1, color: '#5470c680' },
              ],
            },
          },
          lineStyle: { color: '#5470c6' },
          itemStyle: { color: '#5470c6' },
          data: updatedHistory,
        },
      ],
    })
  }, [memoryPercent, memoryTotal, history, usedHistory])

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
        Memory Usage: {memoryPercent.toFixed(1)}%
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
    </div>
  )
}
