import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface GpuChartProps {
  gpuUsage: number | null
  history: number[]
}

export function GpuChart({ gpuUsage, history }: GpuChartProps) {
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

    const updatedHistory = [...history, gpuUsage || 0].slice(-60)

    chartInstance.current.setOption({
      title: {
        text: `GPU Usage: ${(gpuUsage || 0).toFixed(1)}%`,
        left: 'center',
        top: 10,
        textStyle: { fontSize: 14, color: '#fff' },
      },
      tooltip: {
        trigger: 'axis',
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '20%',
        containLabel: true,
      },
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
          name: 'GPU Usage',
          type: 'line',
          smooth: true,
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
  }, [gpuUsage, history])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '200px' }}></div>
    </div>
  )
}

