import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface NetworkChartProps {
  sentRate: number
  recvRate: number
  sentHistory: number[]
  recvHistory: number[]
}

export function NetworkChart({ sentRate, recvRate, sentHistory, recvHistory }: NetworkChartProps) {
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

    const updatedSentHistory = [...sentHistory, sentRate].slice(-60)
    const updatedRecvHistory = [...recvHistory, recvRate].slice(-60)
    
    // 计算最大值用于Y轴
    const maxValue = Math.max(
      ...updatedSentHistory,
      ...updatedRecvHistory,
      1 // 至少为1，避免空图
    )

    const formatBytes = (bytes: number): string => {
      const units = ['B', 'KB', 'MB', 'GB']
      let size = bytes
      let unitIndex = 0
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
      }
      return `${size.toFixed(1)} ${units[unitIndex]}/s`
    }

    chartInstance.current.setOption({
      title: {
        text: `Network: ↑ ${formatBytes(sentRate)} ↓ ${formatBytes(recvRate)}`,
        left: 'center',
        textStyle: { fontSize: 14, color: '#fff' },
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = ''
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${formatBytes(param.value)}<br/>`
          })
          return result
        },
      },
      legend: {
        data: ['Upload', 'Download'],
        top: '10%',
        textStyle: { color: '#aaa' },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '25%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: updatedSentHistory.map((_, i) => i),
        axisLabel: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        name: 'Bytes/s',
        nameTextStyle: { color: '#aaa' },
        axisLabel: { 
          color: '#aaa',
          formatter: (value: number) => {
            const units = ['B', 'KB', 'MB', 'GB']
            let size = value
            let unitIndex = 0
            while (size >= 1024 && unitIndex < units.length - 1) {
              size /= 1024
              unitIndex++
            }
            return `${size.toFixed(1)}${units[unitIndex]}`
          },
        },
        splitLine: { lineStyle: { color: '#333' } },
      },
      series: [
        {
          name: 'Upload',
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
                { offset: 0, color: '#91cc75' },
                { offset: 1, color: '#91cc7580' },
              ],
            },
          },
          lineStyle: { color: '#91cc75' },
          itemStyle: { color: '#91cc75' },
          data: updatedSentHistory,
        },
        {
          name: 'Download',
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
          data: updatedRecvHistory,
        },
      ],
    })
  }, [sentRate, recvRate, sentHistory, recvHistory])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '200px' }}></div>
    </div>
  )
}

