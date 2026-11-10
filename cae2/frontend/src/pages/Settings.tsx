import { FormEvent, useState } from 'react'
import { api, canReview, download } from '../api'
import { useEngagement } from '../App'
import { ErrorNote, Page, useAction } from '../ui'

const SWITCHES: [string, string, string][] = [
  ['einvoice_applicable', 'E-invoicing applies', 'CGST Rule 48(4): aggregate turnover above the notified limit. Turns on the IRN test.'],
  ['tds_194q_applicable', 'TDS on purchase of goods (s.194Q) applies', "Buyer's turnover exceeded ₹10 crore in the preceding year."],
  ['msme_written_agreement', 'Written credit terms with MSME suppliers', 'MSMED s.15: agreed days capped at 45. Off = 15 days.'],
  ['pf_applicable', 'Provident fund applies', 'Turns on the PF short-deduction test.'],
  ['esi_applicable', 'ESI applies', 'Turns on the ESI short-deduction test.'],
]

export default function Settings() {
  const { eng, reload } = useEngagement()
  const [form, setForm] = useState({ materiality: String(eng.materiality), trivial_threshold: String(eng.trivial_threshold), ...eng.settings })
  const { busy, error, run } = useAction()
  const [saved, setSaved] = useState(false)
  const editable = canReview() && !eng.is_closed
  const f = form as Record<string, any>
  const set = (key: string, value: any) => { setForm({ ...form, [key]: value }); setSaved(false) }

  const save = (e: FormEvent) => {
    e.preventDefault()
    run(async () => {
      await api(`/engagements/${eng.id}`, 'PATCH', {
        materiality: Number(f.materiality || 0), trivial_threshold: Number(f.trivial_threshold || 0),
        settings: { ...Object.fromEntries(SWITCHES.map(([k]) => [k, !!f[k]])), rbi_bank_rate_pct: Number(f.rbi_bank_rate_pct || 0), data_as_at: f.data_as_at || null },
      })
      await reload()
      setSaved(true)
    })
  }
  const toggleClosed = () => run(async () => { await api(`/engagements/${eng.id}`, 'PATCH', { is_closed: !eng.is_closed }); await reload() })

  return (
    <Page heading="Engagement settings" sub="Thresholds and applicability the engine cannot work out from the data. Changes take effect on the next audit run.">
      <ErrorNote error={error} />
      <form onSubmit={save} className="card max-w-3xl space-y-5 p-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div><label className="label">Materiality (₹)</label><input className="input" type="number" min="0" disabled={!editable} value={f.materiality} onChange={(e) => set('materiality', e.target.value)} /><p className="mt-1 text-xs text-slate-500">A finding at or above this amount is graded critical.</p></div>
          <div><label className="label">Clearly trivial below (₹)</label><input className="input" type="number" min="0" disabled={!editable} value={f.trivial_threshold} onChange={(e) => set('trivial_threshold', e.target.value)} /><p className="mt-1 text-xs text-slate-500">A finding below this amount steps down one level.</p></div>
          <div><label className="label">Data as at</label><input className="input" type="date" disabled={!editable} value={f.data_as_at || ''} onChange={(e) => set('data_as_at', e.target.value)} /><p className="mt-1 text-xs text-slate-500">Date the uploaded data is complete up to; used for ageing and overdue tests. Blank = today, capped at period end.</p></div>
          <div><label className="label">RBI bank rate (%)</label><input className="input" type="number" min="0" step="0.01" disabled={!editable} value={f.rbi_bank_rate_pct ?? 0} onChange={(e) => set('rbi_bank_rate_pct', e.target.value)} /><p className="mt-1 text-xs text-slate-500">For MSMED s.16 interest (3 × bank rate, monthly rests). 0 = interest not computed. Enter the rate notified by RBI.</p></div>
        </div>
        <div className="space-y-3 border-t border-slate-100 pt-4">
          {SWITCHES.map(([key, label, help]) => (
            <label key={key} className="flex items-start gap-3 text-sm">
              <input type="checkbox" className="mt-1" disabled={!editable} checked={!!f[key]} onChange={(e) => set(key, e.target.checked)} />
              <span><span className="font-medium">{label}</span><span className="block text-xs text-slate-500">{help}</span></span>
            </label>
          ))}
        </div>
        {editable && <div className="flex items-center gap-3"><button className="btn" disabled={busy}>Save settings</button>{saved && <span className="text-sm text-emerald-700">Saved. Run the audit to apply.</span>}</div>}
        {!canReview() && <p className="text-xs text-slate-500">Only a manager or partner can change settings.</p>}
      </form>
      <div className="card mt-6 flex max-w-3xl flex-wrap items-center justify-between gap-3 p-5">
        <div className="text-sm"><div className="font-medium">Working paper</div><div className="text-slate-500">Excel file with findings, evidence, GSTR-2B reconciliation, rules run and review trail.</div></div>
        <div className="flex gap-2">
          <button className="btn-ghost" disabled={busy} onClick={() => run(() => download(`/engagements/${eng.id}/workpaper`, 'working-paper.xlsx'))}>Findings to act on</button>
          <button className="btn-ghost" disabled={busy} onClick={() => run(() => download(`/engagements/${eng.id}/workpaper?include_closed=true`, 'working-paper.xlsx'))}>All findings</button>
        </div>
      </div>
      {canReview() && (
        <div className="card mt-6 flex max-w-3xl flex-wrap items-center justify-between gap-3 p-5">
          <div className="text-sm"><div className="font-medium">{eng.is_closed ? 'Engagement is closed' : 'Close engagement'}</div><div className="text-slate-500">A closed engagement is read-only: no uploads, runs or review changes.</div></div>
          <button className="btn-ghost" disabled={busy} onClick={toggleClosed}>{eng.is_closed ? 'Reopen' : 'Close engagement'}</button>
        </div>
      )}
    </Page>
  )
}
