import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { useEngagement } from '../App'
import { Badge, Empty, ErrorNote, Page, inr, useLoad } from '../ui'

const AREAS = ['Sales', 'Purchases', 'GST', 'TDS', 'Books', 'Treasury', 'Payroll', 'Inventory']
const STATUSES = ['active', 'open', 'queried', 'confirmed', 'dismissed', 'resolved', 'cleared']
const PAGE = 50

export default function Findings() {
  const { eng } = useEngagement()
  const [params, setParams] = useSearchParams()
  const get = (key: string, fallback = '') => params.get(key) ?? fallback
  const status = get('status', 'active')
  const page = Number(get('page', '1'))
  const query = new URLSearchParams({ status, page: String(page), page_size: String(PAGE) })
  for (const key of ['severity', 'area', 'rule', 'fraud', 'q']) if (get(key)) query.set(key, get(key))
  const list = useLoad<any>(() => api(`/engagements/${eng.id}/findings?${query}`), [eng.id, query.toString()])

  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    value ? next.set(key, value) : next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next, { replace: true })
  }
  const select = (key: string, options: string[], all: string, value = get(key)) => (
    <select className="input w-auto" value={value} onChange={(e) => set(key, e.target.value)}>
      <option value="">{all}</option>
      {options.map((o) => <option key={o} value={o}>{o === 'active' ? 'To act on' : o[0].toUpperCase() + o.slice(1)}</option>)}
    </select>
  )
  const pages = Math.ceil((list.data?.total || 0) / PAGE)

  return (
    <Page heading="Findings" sub={list.data ? `${list.data.total} finding(s) · amount involved ${inr(list.data.impact)}` : undefined}>
      <ErrorNote error={list.error} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <select className="input w-auto" value={status} onChange={(e) => set('status', e.target.value)}>
          {STATUSES.map((o) => <option key={o} value={o}>{o === 'active' ? 'To act on' : o[0].toUpperCase() + o.slice(1)}</option>)}
        </select>
        {select('severity', ['critical', 'high', 'medium', 'low'], 'All severities')}
        {select('area', AREAS, 'All areas')}
        <label className="flex items-center gap-1.5 text-sm"><input type="checkbox" checked={get('fraud') === 'true'} onChange={(e) => set('fraud', e.target.checked ? 'true' : '')} /> Fraud indicators only</label>
        <input className="input w-56" placeholder="Search title…" defaultValue={get('q')} onKeyDown={(e) => e.key === 'Enter' && set('q', e.currentTarget.value)} />
        {get('rule') && <button className="btn-ghost" onClick={() => set('rule', '')}>Rule {get('rule')} ✕</button>}
      </div>
      {list.data?.total === 0 && <Empty>No findings match these filters.</Empty>}
      {!!list.data?.items.length && (
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50"><tr>{['Rule', 'Finding', 'Area', 'Severity', 'Amount (₹)', 'Status'].map((h, i) => <th key={h} className={`th ${i === 4 ? 'text-right' : ''}`}>{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">
              {list.data.items.map((f: any) => (
                <tr key={f.id} className="hover:bg-slate-50">
                  <td className="td whitespace-nowrap text-slate-500">{f.rule_code}</td>
                  <td className="td"><Link className="hover:text-indigo-700 hover:underline" to={String(f.id)}>{f.title}</Link>{f.fraud && <span className="ml-2 rounded bg-fuchsia-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-fuchsia-800">Fraud indicator</span>}</td>
                  <td className="td">{f.area}</td>
                  <td className="td"><Badge kind="severity" value={f.severity} /></td>
                  <td className="td whitespace-nowrap text-right tabular-nums">{f.impact ? inr(f.impact).replace('₹', '') : '—'}</td>
                  <td className="td"><Badge kind="status" value={f.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {pages > 1 && (
        <div className="mt-4 flex items-center justify-end gap-2 text-sm">
          <button className="btn-ghost" disabled={page <= 1} onClick={() => set('page', String(page - 1))}>Previous</button>
          <span>Page {page} of {pages}</span>
          <button className="btn-ghost" disabled={page >= pages} onClick={() => set('page', String(page + 1))}>Next</button>
        </div>
      )}
    </Page>
  )
}
