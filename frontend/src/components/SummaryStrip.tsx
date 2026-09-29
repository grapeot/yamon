import { useEffect, useState } from 'react'

interface WindowSummary {
  days: number
  cpu_percent: number | null
  memory_used_gb: number | null
  system_power_w: number | null
  samples: number
  mem_samples: number
  pwr_samples: number
  oldest_ts: number | null
}

// 不足一整天的样本量时不显示数值（避免把几小时的均值当成 3 天均值）
const MIN_SAMPLES_PER_DAY = 86400

function fmt(value: number | null, unit: string): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${value.toFixed(1)}${unit}`
}

export function SummaryStrip() {
  const [windows, setWindows] = useState<WindowSummary[] | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const res = await fetch('/api/summary')
        if (!res.ok) return
        const json = await res.json()
        if (!cancelled && Array.isArray(json.windows)) setWindows(json.windows)
      } catch {
        // 保持上一次成功的数据
      }
    }
    load()
    const id = setInterval(load, 60_000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  const byDays = (d: number) => windows?.find((w) => w.days === d)

  const cell = (
    w: WindowSummary | undefined,
    get: (x: WindowSummary) => number | null,
    unit: string,
    getSamples: (x: WindowSummary) => number
  ) => {
    if (!w || getSamples(w) < MIN_SAMPLES_PER_DAY) {
      return <span className="summary-value dim">—</span>
    }
    const now = Date.now() / 1000
    const coveredDays = w.oldest_ts !== null ? (now - w.oldest_ts) / 86400 : 0
    const partial = coveredDays < w.days - 0.5
    return (
      <span className="summary-value">
        {fmt(get(w), unit)}
        {partial && (
          <span className="summary-partial" title={`recorded ${coveredDays.toFixed(1)} of ${w.days} days`}>
            {Math.max(1, Math.round(coveredDays))}d
          </span>
        )}
      </span>
    )
  }

  const w3 = byDays(3)
  const w7 = byDays(7)
  const w14 = byDays(14)

  return (
    <div className="summary-strip" role="table" aria-label="Multi-day averages">
      <span className="summary-label" role="rowheader">AVG</span>
      <span className="summary-head" role="columnheader">3D</span>
      <span className="summary-head" role="columnheader">7D</span>
      <span className="summary-head" role="columnheader">14D</span>

      <span className="summary-label" role="rowheader">CPU</span>
      {cell(w3, (x) => x.cpu_percent, '%', (x) => x.samples)}
      {cell(w7, (x) => x.cpu_percent, '%', (x) => x.samples)}
      {cell(w14, (x) => x.cpu_percent, '%', (x) => x.samples)}

      <span className="summary-label" role="rowheader">MEM</span>
      {cell(w3, (x) => x.memory_used_gb, 'G', (x) => x.mem_samples)}
      {cell(w7, (x) => x.memory_used_gb, 'G', (x) => x.mem_samples)}
      {cell(w14, (x) => x.memory_used_gb, 'G', (x) => x.mem_samples)}

      <span className="summary-label" role="rowheader">PWR</span>
      {cell(w3, (x) => x.system_power_w, 'W', (x) => x.pwr_samples)}
      {cell(w7, (x) => x.system_power_w, 'W', (x) => x.pwr_samples)}
      {cell(w14, (x) => x.system_power_w, 'W', (x) => x.pwr_samples)}
    </div>
  )
}
