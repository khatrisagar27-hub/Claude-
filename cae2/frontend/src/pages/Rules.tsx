import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, canReview } from '../api'
import { useEngagement } from '../App'
import { Badge, ErrorNote, Page, useAction, useLoad } from '../ui'

const RESULT: Record<string, [string, string]> = {
  ok: ['Run', 'text-emerald-700'], no_data: ['Not run — no data', 'text-amber-700'], disabled: ['Switched off', 'text-slate-500'], error: ['Failed', 'text-red-700 font-semibold'],
}

function RuleRow({ rule, result, engId, editable, onSaved }: { rule: any; result?: any; engId: number; editable: boolean; onSaved: () => void }) {
  const [values, setValues] = useState<Record<string, string>>(Object.fromEntries(rule.params.map((p: any) => [p.name, String(p.value)])))
  const { busy, error, run } = useAction()
  const dirty = rule.params.some((p: any) => String(p.value) !== values[p.name])
  const save = (body: unknown) => run(async () => { await api(`/engagements/${engId}/rules/${rule.code}`, 'PATCH', body); onSaved() })
  const [label, tone] = RESULT[result?.status] || ['Not yet run', 'text-slate-400']

  return (
    <div className={`border-t border-slate-100 px-4 py-3 ${rule.enabled ? '' : 'opacity-60'}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium text-slate-500">{rule.code}</span><span className="font-medium">{rule.name}</span>
            <Badge kind="severity" value={rule.severity} />
            {rule.fraud && <span className="rounded bg-fuchsia-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-fuchsia-800">Fraud indicator</span>}
          </div>
          <p className="mt-1 text-sm text-slate-600">{rule.description}</p>
          {rule.law && <p className="mt-1 text-xs text-slate-500">Provision: {rule.law}</p>}
          <p className="mt-1 text-xs"><span className={tone}>{label}</span>{result?.status === 'no_data' && <span className="text-slate-500"> ({result.error})</span>}
            {rule.active_findings > 0 && <> · <Link className="text-indigo-700 hover:underline" to={`../findings?rule=${rule.code}`}>{rule.active_findings} to act on</Link></>}</p>
          {result?.status === 'error' && <pre className="mt-1 overflow-x-auto rounded bg-red-50 p-2 text-xs text-red-900">{result.error}</pre>}
          <ErrorNote error={error} />
        </div>
        <div className="flex flex-wrap items-end gap-2">
          {rule.params.map((p: any) => (
            <div key={p.name}>
              <label className="label">{p.label}{String(p.default) !== values[p.name] && <span className="text-amber-700"> (default {p.default})</span>}</label>
              <input className="input w-36" type="number" min="0" step="any" disabled={!editable} value={values[p.name]} onChange={(e) => setValues({ ...values, [p.name]: e.target.value })} />
            </div>
          ))}
          {editable && dirty && <button className="btn" disabled={busy} onClick={() => save({ params: Object.fromEntries(Object.entries(values).map(([k, v]) => [k, Number(v)])) })}>Save</button>}
          {editable && <button className="btn-ghost" disabled={busy} onClick={() => save({ enabled: !rule.enabled })}>{rule.enabled ? 'Switch off' : 'Switch on'}</button>}
        </div>
      </div>
    </div>
  )
}

export default function Rules() {
  const { eng } = useEngagement()
  const rules = useLoad<any[]>(() => api(`/engagements/${eng.id}/rules`), [eng.id])
  const runs = useLoad<any[]>(() => api(`/engagements/${eng.id}/runs`), [eng.id])
  const results = Object.fromEntries((runs.data?.[0]?.rules || []).map((r: any) => [r.code, r]))
  const areas = [...new Set(rules.data?.map((r) => r.area))]
  return (
    <Page heading="Rules" sub="Every test the engine runs, the provision behind it and the thresholds it uses. Changes apply to this engagement only and take effect on the next run.">
      <ErrorNote error={rules.error} />
      {areas.map((area) => (
        <div key={area} className="card mb-5 overflow-hidden">
          <h3 className="bg-slate-50 px-4 py-2 text-sm font-semibold">{area}</h3>
          {rules.data!.filter((r) => r.area === area).map((r) => (
            <RuleRow key={r.code + JSON.stringify(r.params) + r.enabled} rule={r} result={results[r.code]} engId={eng.id} editable={canReview() && !eng.is_closed} onSaved={rules.reload} />
          ))}
        </div>
      ))}
    </Page>
  )
}
