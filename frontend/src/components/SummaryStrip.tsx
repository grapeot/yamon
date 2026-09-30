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

interface SummaryPayload {
  windows: WindowSummary[]
  total_recorded_seconds?: number
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
  totalRecorded: number,
) {
  const recorded = window ? sampleSeconds(window) : 0
  // A column appears once its budget of recorded time has accumulated: the
  // column's own length for 5M/1H, one recorded day for longer windows.
  // Gating on the cumulative total (not on this window's coverage) keeps the
  // unflushed minute and sleep gaps from wedging a column at the placeholder.
  if (!window || totalRecorded < Math.min(window.window_seconds, 86400)) {
    return <span key={key} className="summary-value dim">—</span>
  }
  const partial = recorded < window.window_seconds * 0.99
  const coverage = `${Math.round((recorded / window.window_seconds) * 100)}%`
  return <span key={key} className="summary-value">
    {fmt(value(window), unit)}
    {partial && <span className="summary-partial"
      title={`recorded ${(recorded / 3600).toFixed(1)}h of ${(window.window_seconds / 3600).toFixed(1)}h`}>
      {coverage}
    </span>}
  </span>
}

export function SummaryStrip() {
  const [payload, setPayload] = useState<SummaryPayload | null>(null)
  const windows = payload?.windows ?? null
  const totalRecorded = payload?.total_recorded_seconds ?? 0

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const res = await fetch('/api/summary')
        if (!res.ok) return
        const json = await res.json()
        if (!cancelled && Array.isArray(json.windows)) {
          setPayload({ windows: json.windows, total_recorded_seconds: json.total_recorded_seconds })
        }
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
    {WINDOWS.map(({ seconds }) => summaryCell(bySeconds(seconds), value, samples, unit,
      `${label}-${seconds}`, totalRecorded))}
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
