import { api } from '../api'
import { useEngagement } from '../App'
import { ErrorNote, Page, Stat, inr, useLoad } from '../ui'

function Ageing({ heading, block }: { heading: string; block: any }) {
  const max = Math.max(1, ...block.buckets.map((b: any) => b.amount))
  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold">{heading} <span className="font-normal text-slate-500">· {inr(block.total)}</span></h3>
      <div className="mt-3 space-y-2">
        {block.buckets.map((b: any) => (
          <div key={b.bucket} className="flex items-center gap-3 text-sm">
            <span className="w-20 text-slate-600">{b.bucket}</span>
            <span className="h-3 flex-1 rounded bg-slate-100"><span className="block h-3 rounded bg-indigo-500" style={{ width: `${(b.amount / max) * 100}%` }} /></span>
            <span className="w-32 text-right tabular-nums">{inr(b.amount)}</span>
            <span className="w-10 text-right text-xs text-slate-500">{b.invoices}</span>
          </div>
        ))}
      </div>
      <table className="mt-4 min-w-full">
        <thead><tr><th className="th">Largest balances</th><th className="th text-right">Outstanding (₹)</th><th className="th text-right">Oldest (days)</th></tr></thead>
        <tbody className="divide-y divide-slate-100">
          {block.top.map((t: any) => (
            <tr key={t.name}><td className="td">{t.name}</td><td className="td text-right tabular-nums">{inr(t.outstanding).replace('₹', '')}</td><td className="td text-right tabular-nums">{Math.max(0, t.oldest_days)}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function WorkingCapital() {
  const { eng } = useEngagement()
  const wc = useLoad<any>(() => api(`/engagements/${eng.id}/working-capital`), [eng.id])
  const w = wc.data
  const days = (v: number | null) => (v === null ? 'n/a' : `${v} days`)
  return (
    <Page heading="Working capital" sub={w ? `As at ${w.as_at}, over ${w.days} days from the period start. Ageing is by days past due date.` : undefined}>
      <ErrorNote error={wc.error} />
      {w && (<>
        <div className="grid gap-4 md:grid-cols-4">
          <Stat label="Debtor days (DSO)" value={days(w.dso)} note="Receivables ÷ sales × days" />
          <Stat label="Creditor days (DPO)" value={days(w.dpo)} note="Payables ÷ purchases × days" />
          <Stat label="Inventory days (DIO)" value={days(w.dio)} note={w.dio === null ? 'Needs stock movements' : `Stock ${inr(w.stock_value)} ÷ cost issued × days`} />
          <Stat label="Cash conversion cycle" value={days(w.ccc)} note="DSO + DIO − DPO" />
        </div>
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Ageing heading="Receivables" block={w.receivables} />
          <Ageing heading="Payables" block={w.payables} />
        </div>
        <p className="mt-4 text-xs text-slate-500">Sales {inr(w.sales)} and purchases {inr(w.purchases)} are taken gross of GST, as are the balances, so each ratio compares like with like.</p>
      </>)}
    </Page>
  )
}
