import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useEngagement } from '../App'
import { Empty, ErrorNote, Page, RowTable, Stat, inr, title, useLoad } from '../ui'

const ORDER = ['not_in_2b', 'value_mismatch', 'probable_match', 'not_in_books', 'matched']
const HELP: Record<string, string> = {
  not_in_2b: 'ITC claimed in the books; supplier has not reported the invoice.',
  value_mismatch: 'Invoice is in both, but the tax differs.',
  probable_match: 'Same supplier, same taxable value and tax; the invoice number differs. Confirm and correct the number.',
  not_in_books: 'Reported by the supplier, not found in the purchase register.',
  matched: 'In both, tax agrees within ₹1.',
}

export default function Gst() {
  const { eng } = useEngagement()
  const [status, setStatus] = useState('not_in_2b')
  const gst = useLoad<any>(() => api(`/engagements/${eng.id}/gst?status=${status}`), [eng.id, status])
  const g = gst.data
  return (
    <Page heading="GSTR-2B reconciliation" sub="Purchase register against GSTR-2B, matched on supplier GSTIN and invoice number (case, separators and leading zeros ignored).">
      <ErrorNote error={gst.error} />
      {g && !g.ready && <Empty>Upload {g.missing.map((m: string) => (m === 'gstr2b' ? 'GSTR-2B' : 'the purchase register')).join(' and ')} on the <Link className="text-indigo-700 underline" to="../data">Data</Link> tab to reconcile.</Empty>}
      {g?.ready && (<>
        <div className="grid gap-4 md:grid-cols-3">
          <Stat label="ITC claimed in books" value={inr(g.itc_claimed)} />
          <Stat label="Tax as per GSTR-2B" value={inr(g.itc_in_2b)} />
          <Stat label="ITC at risk" value={inr(g.itc_at_risk)} tone="text-red-600" note="Not in 2B + claimed above 2B + marked not available" />
        </div>
        <div className="mt-6 flex flex-wrap gap-2">
          {ORDER.filter((s) => g.statuses[s]).map((s) => (
            <button key={s} onClick={() => setStatus(s)} className={`rounded-md border px-3 py-1.5 text-sm ${status === s ? 'border-indigo-600 bg-indigo-50 font-medium text-indigo-800' : 'border-slate-300 bg-white'}`}>
              {title(s).replace('2b', '2B')} <span className="tabular-nums text-slate-500">{g.statuses[s].lines}</span>
            </button>
          ))}
        </div>
        <p className="mb-3 mt-2 text-sm text-slate-500">{HELP[status]}</p>
        <div className="card overflow-hidden">
          {g.lines.length ? <RowTable rows={g.lines} /> : <div className="p-6 text-sm text-slate-500">No lines with this status.</div>}
        </div>
        {g.total_lines > g.lines.length && <p className="mt-2 text-xs text-slate-500">Showing {g.lines.length} of {g.total_lines}. The working paper has every line.</p>}
      </>)}
    </Page>
  )
}
