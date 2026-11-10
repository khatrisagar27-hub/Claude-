import { Link } from 'react-router-dom'
import { api, download } from '../api'
import { useEngagement } from '../App'
import { BAR, Badge, Empty, ErrorNote, Page, Stat, inr, inrShort, useAction, useLoad, when } from '../ui'

const BAND: Record<string, string> = { critical: 'text-red-600', high: 'text-orange-600', medium: 'text-amber-600', low: 'text-emerald-600' }

export default function Overview() {
  const { eng, reload: reloadEng } = useEngagement()
  const dash = useLoad<any>(() => api(`/engagements/${eng.id}/dashboard`), [eng.id])
  const { busy, error, run } = useAction()
  const d = dash.data

  const runAudit = () => run(async () => { await api(`/engagements/${eng.id}/runs`, 'POST'); await Promise.all([dash.reload(), reloadEng()]) })
  const workpaper = () => run(() => download(`/engagements/${eng.id}/workpaper`, 'working-paper.xlsx'))

  const actions = (<>
    <button className="btn-ghost" onClick={workpaper} disabled={busy || !d?.last_run}>Download working paper</button>
    <button className="btn" onClick={runAudit} disabled={busy || eng.is_closed}>{busy ? 'Working…' : 'Run audit'}</button>
  </>)

  if (!d) return <Page heading="Overview" actions={actions}><ErrorNote error={dash.error || error} /></Page>
  if (!d.last_run) {
    return (
      <Page heading="Overview" actions={actions}>
        <ErrorNote error={error} />
        <Empty>No audit has been run yet. <Link className="text-indigo-700 underline" to="data">Upload data</Link>, then choose Run audit.</Empty>
      </Page>
    )
  }
  const areas = Object.entries<any>(d.risk.areas).sort((a, b) => b[1].score - a[1].score)
  const total = Math.max(1, d.active)
  return (
    <Page heading="Overview" actions={actions}
      sub={<>Last run #{d.last_run.id} on {when(d.last_run.finished_at)} · data as at {d.last_run.as_at}</>}>
      <ErrorNote error={error} />
      {(d.last_run.not_run > 0 || d.last_run.failed > 0) && (
        <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          {d.last_run.failed > 0 && <b>{d.last_run.failed} rule(s) failed to run. </b>}
          {d.last_run.not_run > 0 && <>{d.last_run.not_run} rule(s) were not run because the data they need has not been uploaded. </>}
          <Link className="underline" to="rules">See which</Link>.
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Risk score" value={`${d.risk.overall} / 100`} tone={BAND[d.risk.band]} note={`${d.risk.band} — highest area score`} />
        <Stat label="Findings to act on" value={d.active} note="open, queried or confirmed" />
        <Stat label="Amount involved" value={inrShort(d.impact)} note={inr(d.impact)} />
        <Stat label="Fraud indicators" value={d.fraud_indicators} note={<Link className="text-indigo-700 hover:underline" to="findings?fraud=true">View</Link>} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <div className="card p-4 lg:col-span-2">
          <h3 className="mb-3 text-sm font-semibold">By severity</h3>
          {Object.entries<number>(d.by_severity).map(([sev, n]) => (
            <Link key={sev} to={`findings?severity=${sev}`} className="mb-2 flex items-center gap-3 text-sm hover:opacity-80">
              <span className="w-16 capitalize">{sev}</span>
              <span className="h-3 flex-1 overflow-hidden rounded bg-slate-100"><span className={`block h-3 ${BAR[sev]}`} style={{ width: `${(n / total) * 100}%` }} /></span>
              <span className="w-8 text-right tabular-nums">{n}</span>
            </Link>
          ))}
          <h3 className="mb-2 mt-5 text-sm font-semibold">By review status</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries<number>(d.by_status).map(([status, n]) => (
              <Link key={status} to={`findings?status=${status}`} className="flex items-center gap-1.5 text-sm"><Badge kind="status" value={status} /> {n}</Link>
            ))}
          </div>
        </div>
        <div className="card overflow-hidden lg:col-span-3">
          <h3 className="px-4 pt-4 text-sm font-semibold">Risk by area</h3>
          <table className="mt-2 min-w-full">
            <thead><tr>{['Area', 'Score', 'Critical', 'High', 'Medium', 'Low', 'Amount'].map((h, i) => <th key={h} className={`th ${i > 1 ? 'text-right' : ''}`}>{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">
              {areas.map(([area, a]) => (
                <tr key={area}>
                  <td className="td"><Link className="text-indigo-700 hover:underline" to={`findings?area=${area}`}>{area}</Link></td>
                  <td className="td w-40"><div className="flex items-center gap-2"><span className="h-2 flex-1 rounded bg-slate-100"><span className={`block h-2 rounded ${BAR[a.band]}`} style={{ width: `${a.score}%` }} /></span><span className="w-7 text-right tabular-nums">{a.score}</span></div></td>
                  {['critical', 'high', 'medium', 'low'].map((s) => <td key={s} className="td text-right tabular-nums">{a[s] || ''}</td>)}
                  <td className="td text-right tabular-nums">{inrShort(a.impact)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="px-4 py-3 text-xs text-slate-500">Score = critical ×25 + high ×10 + medium ×4 + low ×1 over findings still to act on, capped at 100.</p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <div className="card overflow-hidden lg:col-span-3">
          <h3 className="px-4 pt-4 text-sm font-semibold">Largest findings</h3>
          <table className="mt-2 min-w-full">
            <tbody className="divide-y divide-slate-100">
              {d.top.map((f: any) => (
                <tr key={f.id}>
                  <td className="td whitespace-nowrap text-slate-500">{f.rule_code}</td>
                  <td className="td"><Link className="hover:text-indigo-700 hover:underline" to={`findings/${f.id}`}>{f.title}</Link></td>
                  <td className="td"><Badge kind="severity" value={f.severity} /></td>
                  <td className="td whitespace-nowrap text-right tabular-nums">{inrShort(f.impact)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card overflow-hidden lg:col-span-2">
          <h3 className="px-4 pt-4 text-sm font-semibold">Run history</h3>
          <table className="mt-2 min-w-full">
            <thead><tr>{['Run', 'Date', 'Risk', 'New', 'Cleared'].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">
              {[...d.trend].reverse().map((t: any) => (
                <tr key={t.run}><td className="td">#{t.run}</td><td className="td whitespace-nowrap">{when(t.date)}</td><td className="td tabular-nums">{t.risk}</td><td className="td tabular-nums">{t.new}</td><td className="td tabular-nums">{t.cleared}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Page>
  )
}
