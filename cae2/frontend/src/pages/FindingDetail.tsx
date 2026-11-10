import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, canReview } from '../api'
import { useEngagement } from '../App'
import { Badge, ErrorNote, Page, RowTable, inr, title, useAction, useLoad, when } from '../ui'

const VERB: Record<string, string> = { open: 'Reopen', queried: 'Mark as queried', confirmed: 'Confirm exception', dismissed: 'Dismiss — not an issue', resolved: 'Mark resolved' }
const NOTE_TONE: Record<string, string> = { query: 'border-violet-200 bg-violet-50', response: 'border-sky-200 bg-sky-50', status: 'border-slate-200 bg-slate-50', comment: 'border-slate-200 bg-white' }

export default function FindingDetail() {
  const { findingId } = useParams()
  const { eng } = useEngagement()
  const finding = useLoad<any>(() => api(`/findings/${findingId}`), [findingId])
  const { busy, error, run } = useAction()
  const [note, setNote] = useState({ kind: 'comment', body: '' })
  const [conclusion, setConclusion] = useState('')
  const [action, setAction] = useState({ description: '', owner: '', due_date: '' })
  const f = finding.data
  if (!f) return <Page heading="Finding"><ErrorNote error={finding.error} /></Page>

  const post = (path: string, body: unknown, after?: () => void, method = 'POST') =>
    run(async () => { finding.setData(await api(path, method, body)); after?.() })
  const locked = eng.is_closed
  const staffMoves = ['open>queried', 'queried>open']
  const allowed = f.allowed.filter((s: string) => canReview() || staffMoves.includes(`${f.status}>${s}`))

  return (
    <Page heading={f.title} sub={<Link className="text-indigo-700 hover:underline" to="..">← All findings</Link>}>
      <ErrorNote error={error} />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="card p-5">
            <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
              <span className="font-medium text-slate-500">{f.rule_code}</span><span>·</span><span>{f.area}</span>
              <Badge kind="severity" value={f.severity} /><Badge kind="status" value={f.status} />
              {f.fraud && <span className="rounded bg-fuchsia-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-fuchsia-800">Fraud indicator</span>}
            </div>
            <p className="text-sm leading-relaxed">{f.detail}</p>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div><dt className="label">Amount involved</dt><dd className="text-lg font-semibold tabular-nums">{f.impact ? inr(f.impact) : 'Not quantified'}</dd></div>
              <div><dt className="label">Provision</dt><dd>{f.law || '—'}</dd></div>
            </dl>
            <p className="mt-3 text-xs text-slate-500">First raised in run #{f.first_run_id}; last seen in run #{f.last_run_id}.</p>
          </div>

          <div className="card overflow-hidden">
            <h3 className="px-5 pt-4 text-sm font-semibold">Evidence ({f.evidence.length} row{f.evidence.length === 1 ? '' : 's'})</h3>
            <div className="mt-2 max-h-[28rem] overflow-auto"><RowTable rows={f.evidence} /></div>
          </div>

          <div className="card p-5">
            <h3 className="mb-3 text-sm font-semibold">Remediation actions</h3>
            {f.actions.length === 0 && <p className="text-sm text-slate-500">None recorded.</p>}
            <ul className="space-y-2">
              {f.actions.map((a: any) => (
                <li key={a.id} className="flex items-start gap-3 text-sm">
                  <input type="checkbox" className="mt-1" checked={a.is_done} disabled={busy || locked} onChange={(e) => post(`/actions/${a.id}`, { is_done: e.target.checked }, undefined, 'PATCH')} />
                  <div className={a.is_done ? 'text-slate-400 line-through' : ''}>{a.description}
                    <div className="text-xs text-slate-500 no-underline">{a.owner || 'No owner'}{a.due_date && ` · due ${a.due_date.split('-').reverse().join('-')}`}</div>
                  </div>
                </li>
              ))}
            </ul>
            {!locked && (
              <form className="mt-4 grid gap-2 sm:grid-cols-6" onSubmit={(e) => { e.preventDefault(); post(`/findings/${f.id}/actions`, { ...action, due_date: action.due_date || null }, () => setAction({ description: '', owner: '', due_date: '' })) }}>
                <input className="input sm:col-span-3" placeholder="Action agreed with management" required value={action.description} onChange={(e) => setAction({ ...action, description: e.target.value })} />
                <input className="input sm:col-span-1" placeholder="Owner" value={action.owner} onChange={(e) => setAction({ ...action, owner: e.target.value })} />
                <input className="input sm:col-span-1" type="date" value={action.due_date} onChange={(e) => setAction({ ...action, due_date: e.target.value })} />
                <button className="btn-ghost sm:col-span-1" disabled={busy}>Add</button>
              </form>
            )}
          </div>
        </div>

        <div className="space-y-6">
          {!locked && allowed.length > 0 && (
            <div className="card p-5">
              <h3 className="mb-2 text-sm font-semibold">Conclusion</h3>
              <textarea className="input mb-3 h-20" placeholder="Basis for the conclusion (required to confirm, dismiss or resolve)" value={conclusion} onChange={(e) => setConclusion(e.target.value)} />
              <div className="flex flex-col gap-2">
                {allowed.map((s: string) => (
                  <button key={s} className={s === 'confirmed' ? 'btn' : 'btn-ghost'} disabled={busy} onClick={() => post(`/findings/${f.id}/status`, { status: s, note: conclusion }, () => setConclusion(''))}>{VERB[s]}</button>
                ))}
              </div>
              {!canReview() && <p className="mt-2 text-xs text-slate-500">Confirming, dismissing and resolving need a manager or partner.</p>}
            </div>
          )}
          <div className="card p-5">
            <h3 className="mb-3 text-sm font-semibold">Review trail</h3>
            <ul className="space-y-2">
              {f.notes.length === 0 && <li className="text-sm text-slate-500">No notes yet.</li>}
              {f.notes.map((n: any) => (
                <li key={n.id} className={`rounded-md border px-3 py-2 text-sm ${NOTE_TONE[n.kind]}`}>
                  <div className="mb-0.5 text-xs text-slate-500">{title(n.kind)} · {n.author} · {when(n.created_at)}</div>
                  <div className="whitespace-pre-wrap">{n.body}</div>
                </li>
              ))}
            </ul>
            {!locked && (
              <form className="mt-4" onSubmit={(e) => { e.preventDefault(); post(`/findings/${f.id}/notes`, note, () => setNote({ ...note, body: '' })) }}>
                <select className="input mb-2" value={note.kind} onChange={(e) => setNote({ ...note, kind: e.target.value })}>
                  <option value="comment">Comment</option><option value="query">Query to management</option><option value="response">Management response</option>
                </select>
                <textarea className="input mb-2 h-20" required value={note.body} onChange={(e) => setNote({ ...note, body: e.target.value })} />
                <button className="btn-ghost w-full" disabled={busy}>Add note</button>
              </form>
            )}
          </div>
        </div>
      </div>
    </Page>
  )
}
