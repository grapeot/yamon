import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface AneChartProps {
  aneUsage: number | null
  history: number[]
}

export function AneChart({ aneUsage, history }: AneChartProps) {
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

    const updatedHistory = [...history, aneUsage || 0].slice(-120)

    chartInstance.current.setOption({
      title: {
        text: `ANE Usage: ${(aneUsage || 0).toFixed(1)}%`,
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
        nameTextStyle: { color: '#aaa' },
        axisLabel: { color: '#aaa' },
        splitLine: { lineStyle: { color: '#333' } },
      },
      series: [
        {
          name: 'ANE Usage',
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
                { offset: 0, color: '#9a60b4' },
                { offset: 1, color: '#9a60b480' },
              ],
            },
          },
          lineStyle: { color: '#9a60b4' },
          itemStyle: { color: '#9a60b4' },
          data: updatedHistory,
        },
      ],
    })
  }, [aneUsage, history])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '200px' }}></div>
    </div>
  )
}

