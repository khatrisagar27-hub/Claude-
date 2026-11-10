import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, canReview } from '../api'
import type { Engagement } from '../App'
import { Empty, ErrorNote, Page, useAction, useLoad } from '../ui'

const KINDS = ['internal_audit', 'statutory_audit', 'tax_audit', 'gst_review']

function fyDefaults() {
  const now = new Date()
  const start = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1
  return { period_start: `${start}-04-01`, period_end: `${start + 1}-03-31`, name: `FY ${start}-${String(start + 1).slice(2)}` }
}

export default function Engagements() {
  const navigate = useNavigate()
  const list = useLoad<Engagement[]>(() => api('/engagements'))
  const clients = useLoad<any[]>(() => api('/clients'))
  const [show, setShow] = useState(false)
  const [form, setForm] = useState({ client_id: 'new', client_name: '', pan: '', gstin: '', kind: 'internal_audit', materiality: '', trivial_threshold: '', ...fyDefaults() })
  const { busy, error, run } = useAction()
  const set = (key: string) => (e: any) => setForm({ ...form, [key]: e.target.value })

  const create = (e: FormEvent) => {
    e.preventDefault()
    run(async () => {
      const clientId = form.client_id === 'new'
        ? (await api('/clients', 'POST', { name: form.client_name, pan: form.pan || null, gstin: form.gstin || null })).id
        : Number(form.client_id)
      const eng = await api('/engagements', 'POST', {
        client_id: clientId, name: form.name, kind: form.kind, period_start: form.period_start, period_end: form.period_end,
        materiality: Number(form.materiality || 0), trivial_threshold: Number(form.trivial_threshold || 0),
      })
      navigate(`/e/${eng.id}/data`)
    })
  }

  return (
    <Page heading="Engagements" sub="Each engagement is one client for one period. Data, findings and working papers all belong to an engagement."
      actions={canReview() && <button className="btn" onClick={() => setShow(!show)}>{show ? 'Cancel' : 'New engagement'}</button>}>
      <ErrorNote error={list.error} />
      {show && (
        <form onSubmit={create} className="card mb-6 grid gap-4 p-5 md:grid-cols-3">
          <div className="md:col-span-3"><ErrorNote error={error} /></div>
          <div>
            <label className="label">Client</label>
            <select className="input" value={form.client_id} onChange={set('client_id')}>
              <option value="new">+ New client</option>
              {clients.data?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          {form.client_id === 'new' && (<>
            <div><label className="label">Client name</label><input className="input" required value={form.client_name} onChange={set('client_name')} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">PAN</label><input className="input uppercase" value={form.pan} onChange={set('pan')} maxLength={10} /></div>
              <div><label className="label">GSTIN</label><input className="input uppercase" value={form.gstin} onChange={set('gstin')} maxLength={15} /></div>
            </div>
          </>)}
          <div><label className="label">Engagement name</label><input className="input" required value={form.name} onChange={set('name')} /></div>
          <div>
            <label className="label">Type</label>
            <select className="input" value={form.kind} onChange={set('kind')}>{KINDS.map((k) => <option key={k} value={k}>{k.replace('_', ' ')}</option>)}</select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Period from</label><input className="input" type="date" required value={form.period_start} onChange={set('period_start')} /></div>
            <div><label className="label">Period to</label><input className="input" type="date" required value={form.period_end} onChange={set('period_end')} /></div>
          </div>
          <div><label className="label">Materiality (₹)</label><input className="input" type="number" min="0" value={form.materiality} onChange={set('materiality')} placeholder="Findings at or above this become critical" /></div>
          <div><label className="label">Clearly trivial below (₹)</label><input className="input" type="number" min="0" value={form.trivial_threshold} onChange={set('trivial_threshold')} placeholder="Findings below this step down one level" /></div>
          <div className="flex items-end"><button className="btn" disabled={busy}>Create and upload data</button></div>
        </form>
      )}
      {list.data?.length === 0 && <Empty>No engagements yet.{canReview() ? ' Create one to begin.' : ' Ask a manager or partner to create one.'}</Empty>}
      {!!list.data?.length && (
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50"><tr>{['Client', 'Engagement', 'Type', 'Period', 'To review', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">
              {list.data.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50">
                  <td className="td font-medium"><Link className="text-indigo-700 hover:underline" to={`/e/${e.id}`}>{e.client_name}</Link></td>
                  <td className="td">{e.name}</td>
                  <td className="td capitalize">{e.kind.replace('_', ' ')}</td>
                  <td className="td whitespace-nowrap">{e.period_start.split('-').reverse().join('-')} to {e.period_end.split('-').reverse().join('-')}</td>
                  <td className="td tabular-nums">{e.open_findings}</td>
                  <td className="td text-right">{e.is_closed && <span className="rounded bg-slate-200 px-2 py-0.5 text-xs">Closed</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Page>
  )
}
