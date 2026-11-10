import { ReactNode, useCallback, useEffect, useState } from 'react'

const rupee = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 })
export const inr = (value: number | null | undefined) => rupee.format(Number(value || 0))
export const inrShort = (value: number) => {
  const v = Math.abs(value)
  if (v >= 1e7) return `₹${(value / 1e7).toFixed(2)} Cr`
  if (v >= 1e5) return `₹${(value / 1e5).toFixed(2)} L`
  return rupee.format(value)
}
export const when = (iso?: string | null) => (iso ? new Date(iso + (iso.length > 10 && !iso.endsWith('Z') ? 'Z' : '')).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: iso.length > 10 ? 'short' : undefined }) : '—')
export const title = (text: string) => text.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())

const SEVERITY: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 ring-red-200',
  high: 'bg-orange-100 text-orange-800 ring-orange-200',
  medium: 'bg-amber-100 text-amber-800 ring-amber-200',
  low: 'bg-slate-100 text-slate-700 ring-slate-200',
}
const STATUS: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800 ring-blue-200',
  queried: 'bg-violet-100 text-violet-800 ring-violet-200',
  confirmed: 'bg-red-100 text-red-800 ring-red-200',
  dismissed: 'bg-slate-100 text-slate-600 ring-slate-200',
  resolved: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  cleared: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
}
export const BAR: Record<string, string> = { critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-amber-400', low: 'bg-slate-400' }

export function Badge({ kind, value }: { kind: 'severity' | 'status'; value: string }) {
  const tone = (kind === 'severity' ? SEVERITY : STATUS)[value] || SEVERITY.low
  return <span className={`inline-block whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${tone}`}>{title(value)}</span>
}

export function Page({ heading, sub, actions, children }: { heading: string; sub?: ReactNode; actions?: ReactNode; children: ReactNode }) {
  return (
    <div className="mx-auto max-w-7xl px-6 py-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">{heading}</h1>
          {sub && <p className="mt-1 max-w-3xl text-sm text-slate-500">{sub}</p>}
        </div>
        <div className="flex flex-wrap gap-2">{actions}</div>
      </div>
      {children}
    </div>
  )
}

export function Stat({ label, value, note, tone }: { label: string; value: ReactNode; note?: ReactNode; tone?: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${tone || ''}`}>{value}</div>
      {note && <div className="mt-1 text-xs text-slate-500">{note}</div>}
    </div>
  )
}

export function ErrorNote({ error }: { error?: string | null }) {
  return error ? <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div> : null
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="card px-6 py-10 text-center text-sm text-slate-500">{children}</div>
}

/** Loads data on mount and whenever deps change; reload() refetches. */
export function useLoad<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const reload = useCallback(() => {
    setLoading(true)
    return loader()
      .then((d) => { setData(d); setError(null) })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, deps)
  useEffect(() => { reload() }, [reload])
  return { data, error, loading, reload, setData }
}

/** Runs an action with busy and error state. */
export function useAction() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError(null)
    try {
      await fn()
      return true
    } catch (e) {
      setError((e as Error).message)
      return false
    } finally {
      setBusy(false)
    }
  }
  return { busy, error, run, setError }
}

/** Generic table for evidence and similar row lists: columns come from the first row. */
export function RowTable({ rows, money = [] }: { rows: Record<string, any>[]; money?: string[] }) {
  if (!rows.length) return <div className="text-sm text-slate-500">No rows.</div>
  const columns = Object.keys(rows[0])
  // A column is numeric if any row holds a number in it; counts and percentages are shown plain.
  const numeric = new Set(columns.filter((c) => rows.some((r) => typeof r[c] === 'number')))
  const plain = (c: string) => /pct|days|digit|row$|rate_applied|^fy$/.test(c)
  const isMoney = (c: string) => money.includes(c) || (numeric.has(c) && !plain(c))
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>{columns.map((c) => <th key={c} className={`th ${numeric.has(c) ? 'text-right' : ''}`}>{title(c)}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c} className={`td whitespace-nowrap ${numeric.has(c) ? 'text-right tabular-nums' : ''}`}>
                  {row[c] === null || row[c] === '' ? <span className="text-slate-300">—</span>
                    : typeof row[c] === 'boolean' ? (row[c] ? 'Yes' : 'No')
                    : typeof row[c] === 'number' && isMoney(c) ? inr(row[c]).replace('₹', '') : String(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
