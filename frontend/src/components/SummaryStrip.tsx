import { useEffect, useState } from 'react'

interface WindowSummary {
  window_seconds: number
  cpu_percent: number | null
  memory_used_gb: number | null
  system_power_w: number | null
  temperature_c: number | null
  samples: number
  mem_samples: number
  pwr_samples: number
  temp_samples: number
}

const WINDOWS = [
  { seconds: 3600, label: '1H' },
  { seconds: 86400, label: '1D' },
  { seconds: 3 * 86400, label: '3D' },
  { seconds: 7 * 86400, label: '7D' },
  { seconds: 14 * 86400, label: '14D' },
] as const

function fmt(value: number | null, unit: string): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${value.toFixed(1)}${unit}`
}

function summaryCell(
  window: WindowSummary | undefined,
  value: (item: WindowSummary) => number | null,
  sampleSeconds: (item: WindowSummary) => number,
  unit: string,
  key: string,
) {
  const recorded = window ? sampleSeconds(window) : 0
  // 1H needs a complete hour; longer windows need at least one recorded day.
  if (!window || recorded < Math.min(window.window_seconds, 86400)) {
    return <span key={key} className="summary-value dim">—</span>
  }
  const partial = recorded < window.window_seconds * 0.99
  const coverage = `${(recorded / 86400).toFixed(1)}d`
  return <span key={key} className="summary-value">
    {fmt(value(window), unit)}
    {partial && <span className="summary-partial"
      title={`recorded ${coverage} of ${window.window_seconds / 86400} days`}>
      {coverage}
    </span>}
  </span>
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
        // Keep the last successful values during a transient failure.
      }
    }
    load()
    const id = setInterval(load, 60_000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  const bySeconds = (seconds: number) => windows?.find((w) => w.window_seconds === seconds)
  const row = (label: string, value: (w: WindowSummary) => number | null,
    samples: (w: WindowSummary) => number, unit: string) => <>
    <span className="summary-label" role="rowheader">{label}</span>
    {WINDOWS.map(({ seconds }) => summaryCell(bySeconds(seconds), value, samples, unit, `${label}-${seconds}`))}
  </>

  return <div className="summary-strip" role="table" aria-label="Multi-window averages">
    <span className="summary-label" role="rowheader">AVG</span>
    {WINDOWS.map(({ seconds, label }) => <span key={seconds} className="summary-head" role="columnheader">{label}</span>)}
    {row('CPU', (w) => w.cpu_percent, (w) => w.samples, '%')}
    {row('MEM', (w) => w.memory_used_gb, (w) => w.mem_samples, 'G')}
    {row('PWR', (w) => w.system_power_w, (w) => w.pwr_samples, 'W')}
    {row('TEMP', (w) => w.temperature_c, (w) => w.temp_samples, '°C')}
  </div>
}
