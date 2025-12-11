import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface GpuChartProps {
  gpuUsage: number | null
  gpuFreqMhz: number | null
  history: number[]
}

export function GpuChart({ gpuUsage, gpuFreqMhz, history }: GpuChartProps) {
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

    const updatedHistory = [...history, gpuUsage || 0].slice(-120)

    chartInstance.current.setOption({
      title: {
        show: false, // Hide ECharts title, we'll use HTML text instead for selectability
      },
      tooltip: {
        trigger: 'axis',
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
          name: 'GPU Usage',
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
                { offset: 0, color: '#fac858' },
                { offset: 1, color: '#fac85880' },
              ],
            },
          },
          lineStyle: { color: '#fac858' },
          itemStyle: { color: '#fac858' },
          data: updatedHistory,
        },
      ],
    })
  }, [gpuUsage, gpuFreqMhz, history])

  const titleText = gpuFreqMhz !== null
    ? `GPU Usage: ${(gpuUsage || 0).toFixed(1)}% (${gpuFreqMhz.toFixed(0)} MHz)`
    : `GPU Usage: ${(gpuUsage || 0).toFixed(1)}%`

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

