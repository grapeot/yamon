import React from 'react'

interface MetricCardProps {
  title: string
  value: string | number | null
  unit?: string
  className?: string
}

export function MetricCard({ title, value, unit = '', className = '' }: MetricCardProps) {
  const displayValue = value !== null ? `${value}${unit}` : 'N/A'
  
  return (
    <div className={`metric-card ${className}`}>
      <div className="metric-title">{title}</div>
      <div className="metric-value">{displayValue}</div>
    </div>
  )
}

