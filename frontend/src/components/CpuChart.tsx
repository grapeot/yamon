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

    const updatedHistory = [...history, cpuPercent].slice(-60)
    
    // 生成16种不同的颜色
    const colors = [
      '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
      '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ff9f7f',
      '#ffdb5c', '#ff6e76', '#e690d1', '#9c88ff', '#6bcf82', '#ffa940'
    ]

    // 准备每核心的历史数据
    // 由于我们只有总体CPU历史，我们使用当前每核心的比例来创建堆叠图
    const totalCurrentCoreUsage = cpuPerCore.reduce((sum, val) => sum + val, 0) || cpuPercent || 1
    
    const coreSeries = cpuPerCore.map((currentValue, coreIdx) => {
      const ratio = totalCurrentCoreUsage > 0 ? currentValue / totalCurrentCoreUsage : 0
      return {
        name: `Core ${coreIdx}`,
        type: 'line',
        stack: 'CPU',
        areaStyle: { opacity: 0.4 },
        showSymbol: false,
        // 根据当前比例分配历史数据
        data: updatedHistory.map((total) => ratio * total),
        lineStyle: { color: colors[coreIdx % colors.length], width: 1 },
        itemStyle: { color: colors[coreIdx % colors.length] },
      }
    })

    chartInstance.current.setOption({
      title: {
        text: `CPU Usage: ${cpuPercent.toFixed(1)}%`,
        left: 'center',
        top: 10,
        textStyle: { fontSize: 14, color: '#fff' },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: {
        show: false, // 隐藏图例，因为16个核心太多
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
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
      series: coreSeries,
    })
  }, [cpuPercent, cpuPerCore, history])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '200px' }}></div>
    </div>
  )
}

